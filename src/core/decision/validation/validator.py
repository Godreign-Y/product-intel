import datetime
import threading
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import scipy.stats as stats

from src.core.decision.config_loader import load_decision_config
from src.core.decision.validation.adjudicator import adjudicate
from src.core.decision.validation.coherence import check_multi_kpi_coherence
from src.core.decision.validation.plausibility import check_plausibility
from src.core.decision.validation.resolver import (
    ResolvedHypothesis,
    get_product_frame,
    resolve_hypothesis,
)
from src.core.forecaster import ProductForecaster
from src.core.sensitivity import SensitivityEngine
from src.core.simulator import ScenarioSimulator
from src.utils.logger import setup_logger

logger = setup_logger("validation_engine")


def _direction_label(value: float, negligible: float) -> str:
    if abs(value) < negligible:
        return "neutral"
    return "positive" if value > 0 else "negative"


def _direction_match(expected: str, actual: str) -> Optional[bool]:
    if expected == "neutral" or actual == "neutral":
        return None
    return expected == actual


def _strength_from_delta(delta_pct: float, max_scale: float = 25.0) -> float:
    return min(1.0, abs(delta_pct) / max_scale)


class ValidationEngine:
    def __init__(
        self,
        df_historical: Optional[pd.DataFrame],
        forecaster: ProductForecaster,
        sensitivity_engine: SensitivityEngine,
        simulator: ScenarioSimulator,
        explainer: Optional[Any] = None,
    ):
        self._thread_local = threading.local()
        self._default_df = df_historical
        self.forecaster = forecaster
        self.sensitivity_engine = sensitivity_engine
        self.simulator = simulator
        self.explainer = explainer
        self._sensitivity_cache: Dict[str, Dict[str, Any]] = {}

        cfg = load_decision_config()
        val_cfg = cfg.get("validation", {})
        self.forecast_horizon = val_cfg.get("forecast_horizon_days", 14)
        self.negligible_effect_pct = float(val_cfg.get("negligible_effect_pct", 2.0))
        self.causal_min_rows = val_cfg.get("causal_min_rows", 20)
        self.causal_p_inconclusive = float(val_cfg.get("causal_p_inconclusive", 0.10))
        self.correlation_min_rows = val_cfg.get("correlation_min_rows", 10)
        self.max_lag_days = int(val_cfg.get("max_lag_days", 7))
        self.shap_top_n = int(val_cfg.get("shap_top_n_features", 8))
        self.signal_weights = val_cfg.get("signal_weights", {})

    def clear_caches(self) -> None:
        self._sensitivity_cache.clear()

    @property
    def df(self) -> Optional[pd.DataFrame]:
        if not hasattr(self._thread_local, "df"):
            return self._default_df
        return self._thread_local.df

    @df.setter
    def df(self, value: Optional[pd.DataFrame]):
        self._thread_local.df = value

    def validate(
        self,
        hypothesis: Dict[str, Any],
        product_id: str = "P001",
        query_pcts: Optional[Dict[str, float]] = None,
        historical_evidence: Optional[List[Dict[str, Any]]] = None,
        run_shap: bool = True,
    ) -> Dict[str, Any]:
        logger.info(
            "validate: hypothesis='%s' product=%s",
            hypothesis.get("hypothesis_id"),
            product_id,
        )
        original_df = self.df
        if self.df is None:
            from src.api.dependencies import get_historical_df_from_db

            self.df = get_historical_df_from_db(product_id=product_id)

        try:
            resolved = resolve_hypothesis(hypothesis, self.df, product_id, query_pcts)
            negligible = self.negligible_effect_pct

            forecast_raw, kpi_deltas = self._run_forecast_signal(resolved, product_id)
            sensitivity_raw = self._run_sensitivity_signal(resolved, product_id)
            correlation_raw = self._run_correlation_signal(resolved, product_id)
            causal_raw = self._run_causal_signal(resolved, product_id)
            historical_raw = self._run_historical_signal(
                resolved, historical_evidence or []
            )
            shap_raw = (
                self._run_shap_signal(resolved)
                if run_shap and self.explainer is not None
                else self._skipped_signal("shap", "explainer_unavailable")
            )

            multi_kpi = check_multi_kpi_coherence(
                resolved.driver_col, kpi_deltas, negligible
            )
            plausibility = check_plausibility(resolved.driver_col, kpi_deltas)

            signals = {
                "forecast": self._normalize_forecast(forecast_raw, resolved, negligible),
                "sensitivity": self._normalize_sensitivity(sensitivity_raw, resolved, negligible),
                "correlation": self._normalize_correlation(correlation_raw, resolved, negligible),
                "causal": self._normalize_causal(causal_raw, resolved, negligible),
                "historical": self._normalize_historical(historical_raw, resolved),
                "shap": self._normalize_shap(shap_raw, resolved),
            }
            for name, sig in signals.items():
                sig["weight"] = float(self.signal_weights.get(name, 0.1))

            adjudication = adjudicate(signals, resolved, plausibility, multi_kpi)

            return {
                "correlation": correlation_raw,
                "sensitivity": sensitivity_raw,
                "forecast_simulation": forecast_raw.get("primary", {}),
                "forecast_by_kpi": forecast_raw.get("by_kpi", {}),
                "causal": causal_raw,
                "historical_experiments": historical_raw,
                "shap": shap_raw,
                "signals": signals,
                "families": adjudication.get("families", {}),
                "multi_kpi_coherence": multi_kpi,
                "plausibility": plausibility,
                "adjudication": adjudication,
                "change_pct_used": resolved.change_pct,
                "driver_col": resolved.driver_col,
                "driver_key": resolved.driver_key,
                "primary_kpi": resolved.primary_kpi,
                "kpi_cols": resolved.kpi_cols,
                "validated_at": datetime.datetime.utcnow().isoformat(),
            }
        finally:
            self.df = original_df

    def _skipped_signal(self, name: str, reason: str) -> Dict[str, Any]:
        return {"name": name, "status": "skipped", "reason": reason}

    def _run_forecast_signal(
        self, resolved: ResolvedHypothesis, product_id: str
    ) -> tuple[Dict[str, Any], Dict[str, float]]:
        kpi_deltas: Dict[str, float] = {}
        by_kpi: Dict[str, Any] = {}
        primary_payload: Dict[str, Any] = {
            "baseline_forecast": 0.0,
            "simulated_forecast": 0.0,
            "expected_delta": 0.0,
            "delta_pct": 0.0,
            "status": "insufficient_data",
        }

        if self.df is None or self.df.empty:
            return {"primary": primary_payload, "by_kpi": by_kpi}, kpi_deltas

        pct = resolved.change_pct
        sign = "+" if pct >= 0 else ""
        change_str = f"{resolved.driver_key} {sign}{pct:g}%"

        try:
            sim = self.simulator.evaluate_scenario(
                historical_df=self.df,
                product_id=product_id,
                horizon_days=self.forecast_horizon,
                changes=[change_str],
            )
            for kpi in resolved.kpi_cols:
                if kpi not in sim.get("kpis", {}):
                    continue
                summary = sim["kpis"][kpi]
                delta_pct = float(summary.get("percentage_difference", 0.0))
                kpi_deltas[kpi] = delta_pct
                by_kpi[kpi] = {
                    "baseline": summary.get("baseline"),
                    "simulated": summary.get("simulated"),
                    "absolute_difference": summary.get("absolute_difference"),
                    "delta_pct": delta_pct,
                    "impact": summary.get("impact"),
                }

            if resolved.primary_kpi in by_kpi:
                p = by_kpi[resolved.primary_kpi]
                primary_payload = {
                    "baseline_forecast": p.get("baseline", 0.0),
                    "simulated_forecast": p.get("simulated", 0.0),
                    "expected_delta": p.get("absolute_difference", 0.0),
                    "delta_pct": p.get("delta_pct", 0.0),
                    "status": "ok",
                    "change_str": change_str,
                }
            else:
                primary_payload["status"] = "error"
        except Exception as exc:
            logger.error("Forecast signal failed: %s", exc)
            primary_payload["status"] = "error"
            primary_payload["error"] = str(exc)

        return {"primary": primary_payload, "by_kpi": by_kpi}, kpi_deltas

    def _sensitivity_cache_key(self, product_id: str, target_metric: str) -> str:
        return f"{product_id}:{target_metric}:{self.forecast_horizon}"

    def _run_sensitivity_signal(
        self, resolved: ResolvedHypothesis, product_id: str
    ) -> Dict[str, Any]:
        cache_key = self._sensitivity_cache_key(product_id, resolved.primary_kpi)
        if cache_key not in self._sensitivity_cache:
            try:
                self._sensitivity_cache[cache_key] = (
                    self.sensitivity_engine.calculate_sensitivity(
                        historical_df=self.df,
                        product_id=product_id,
                        horizon_days=self.forecast_horizon,
                        target_metric=resolved.primary_kpi,
                    )
                )
            except Exception as exc:
                logger.error("Sensitivity cache fill failed: %s", exc)
                self._sensitivity_cache[cache_key] = {}

        all_sens = self._sensitivity_cache.get(cache_key, {})
        return all_sens.get(
            resolved.driver_key,
            {"elasticity_score": 0.0, "expected_impact": 0.0, "confidence": "Low", "status": "missing"},
        )

    def _run_correlation_signal(
        self, resolved: ResolvedHypothesis, product_id: str
    ) -> Dict[str, Any]:
        prod = get_product_frame(self.df, product_id)
        if len(prod) < self.correlation_min_rows:
            return {
                "status": "insufficient_data",
                "pearson": 0.0,
                "spearman": 0.0,
                "p_value": 1.0,
                "mi_score": 0.0,
                "best_lag": 0,
            }

        driver = resolved.driver_col
        kpi = resolved.primary_kpi
        if driver not in prod.columns or kpi not in prod.columns:
            return {"status": "insufficient_data", "pearson": 0.0, "spearman": 0.0, "p_value": 1.0}

        best = {"pearson": 0.0, "spearman": 0.0, "p_value": 1.0, "mi_score": 0.0, "best_lag": 0}
        for lag in range(0, self.max_lag_days + 1):
            x = prod[driver].astype(float).values
            y = prod[kpi].astype(float).shift(-lag).values if lag else prod[kpi].astype(float).values
            mask = ~np.isnan(x) & ~np.isnan(y)
            if mask.sum() < self.correlation_min_rows:
                continue
            x, y = x[mask], y[mask]
            try:
                p_coef, p_val = stats.pearsonr(x, y)
                s_coef, _ = stats.spearmanr(x, y)
                if np.isnan(p_coef):
                    p_coef = 0.0
                if np.isnan(p_val):
                    p_val = 1.0
                if abs(p_coef) > abs(best["pearson"]):
                    mi_score = 0.0
                    try:
                        from sklearn.feature_selection import mutual_info_regression

                        mi_vals = mutual_info_regression(x.reshape(-1, 1), y, random_state=42)
                        mi_score = round(float(mi_vals[0]), 4)
                    except Exception:
                        pass
                    best = {
                        "pearson": round(float(p_coef), 4),
                        "spearman": round(float(s_coef), 4),
                        "p_value": round(float(p_val), 4),
                        "mi_score": mi_score,
                        "best_lag": lag,
                        "status": "ok",
                    }
            except Exception as exc:
                logger.warning("Lag correlation failed lag=%s: %s", lag, exc)

        if "status" not in best:
            best["status"] = "ok"
        return best

    def _run_causal_signal(
        self, resolved: ResolvedHypothesis, product_id: str
    ) -> Dict[str, Any]:
        prod = get_product_frame(self.df, product_id)
        driver, kpi = resolved.driver_col, resolved.primary_kpi
        if (
            len(prod) < self.causal_min_rows
            or driver not in prod.columns
            or kpi not in prod.columns
        ):
            return {
                "ate_estimate": 0.0,
                "p_value": 1.0,
                "status": "insufficient_data",
                "method": "Insufficient data",
            }

        driver_vals = prod[driver].astype(float).values
        kpi_vals = prod[kpi].astype(float).values
        lower_bound = np.percentile(driver_vals, 33.3)
        upper_bound = np.percentile(driver_vals, 66.7)
        control = kpi_vals[driver_vals <= lower_bound]
        treatment = kpi_vals[driver_vals >= upper_bound]

        if len(treatment) < 5 or len(control) < 5:
            return {
                "ate_estimate": 0.0,
                "p_value": 1.0,
                "status": "insufficient_data",
                "method": "Insufficient groups",
            }

        ate = float(np.mean(treatment) - np.mean(control))
        try:
            _, p_val = stats.ttest_ind(treatment, control, equal_var=False)
            if np.isnan(p_val):
                p_val = 1.0
        except Exception:
            p_val = 1.0

        kpi_std = float(np.std(kpi_vals)) or 1.0
        normalized_ate = ate / kpi_std

        return {
            "ate_estimate": round(ate, 4),
            "normalized_ate": round(normalized_ate, 4),
            "p_value": round(float(p_val), 4),
            "status": "ok",
            "method": "ATE Proxy (Tertile Split, Welch's T-Test)",
            "n_treatment": int(len(treatment)),
            "n_control": int(len(control)),
        }

    def _run_historical_signal(
        self,
        resolved: ResolvedHypothesis,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not evidence:
            return {
                "status": "insufficient_data",
                "matches": 0,
                "positive_rate": 0.0,
                "avg_improvement_pct": 0.0,
            }

        positives = [e for e in evidence if e.get("outcome") == "positive"]
        improvements = [
            float(e.get("improvement_pct", 0))
            for e in evidence
            if e.get("improvement_pct") is not None
        ]
        return {
            "status": "ok",
            "matches": len(evidence),
            "positive_rate": round(len(positives) / len(evidence), 4),
            "avg_improvement_pct": round(
                float(np.mean(improvements)) if improvements else 0.0, 2
            ),
            "items": evidence[:5],
        }

    def _run_shap_signal(self, resolved: ResolvedHypothesis) -> Dict[str, Any]:
        try:
            features = self.explainer.get_global_importance(resolved.primary_kpi)
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

        rank = None
        for idx, feat in enumerate(features[: self.shap_top_n]):
            feat_name = str(feat.get("feature", "")).lower()
            if resolved.driver_col in feat_name or resolved.driver_key in feat_name:
                rank = idx + 1
                break

        return {
            "status": "ok",
            "rank": rank,
            "top_n": self.shap_top_n,
            "aligned": rank is not None,
        }

    def _normalize_forecast(
        self, raw: Dict[str, Any], resolved: ResolvedHypothesis, negligible: float
    ) -> Dict[str, Any]:
        primary = raw.get("primary", {})
        delta = float(primary.get("delta_pct", 0.0))
        actual = _direction_label(delta, negligible)
        expected = resolved.expected_direction
        match = _direction_match(expected, actual)
        status = primary.get("status", "error")
        if status == "ok" and abs(delta) < negligible:
            match = None
        return {
            "name": "forecast",
            "status": status,
            "direction": actual,
            "direction_match": match,
            "strength": _strength_from_delta(delta),
            "confidence": 0.9 if status == "ok" else 0.0,
            "delta_pct": delta,
        }

    def _normalize_sensitivity(
        self, raw: Dict[str, Any], resolved: ResolvedHypothesis, negligible: float
    ) -> Dict[str, Any]:
        elasticity = float(raw.get("elasticity_score", 0.0))
        impact = float(raw.get("expected_impact", 0.0))
        conf_tier = str(raw.get("confidence", "Low"))
        conf_map = {"High": 0.85, "Medium": 0.6, "Low": 0.35}
        actual = _direction_label(impact, negligible)
        expected = resolved.expected_direction
        status = "ok" if raw.get("status") != "missing" else "insufficient_data"
        return {
            "name": "sensitivity",
            "status": status,
            "direction": actual,
            "direction_match": _direction_match(expected, actual),
            "strength": min(1.0, abs(elasticity)),
            "confidence": conf_map.get(conf_tier, 0.35),
            "elasticity_score": elasticity,
        }

    def _normalize_correlation(
        self, raw: Dict[str, Any], resolved: ResolvedHypothesis, negligible: float
    ) -> Dict[str, Any]:
        pearson = float(raw.get("pearson", 0.0))
        p_val = float(raw.get("p_value", 1.0))
        actual = _direction_label(pearson, 0.05)
        expected = resolved.expected_direction
        status = raw.get("status", "ok")
        significant = p_val < 0.05
        strength = min(1.0, (abs(pearson) + abs(float(raw.get("mi_score", 0.0)))) / 2.0)
        match = _direction_match(expected, actual) if significant else None
        if significant and match is False:
            pass
        elif not significant:
            match = None
        return {
            "name": "correlation",
            "status": status,
            "direction": actual,
            "direction_match": match,
            "strength": strength,
            "confidence": 0.7 if significant else 0.25,
            "best_lag": raw.get("best_lag", 0),
        }

    def _normalize_causal(
        self, raw: Dict[str, Any], resolved: ResolvedHypothesis, negligible: float
    ) -> Dict[str, Any]:
        ate = float(raw.get("ate_estimate", 0.0))
        p_val = float(raw.get("p_value", 1.0))
        status = raw.get("status", "ok")
        actual = _direction_label(ate, negligible)
        expected = resolved.expected_direction
        if p_val > self.causal_p_inconclusive:
            match = None
            status = "inconclusive" if status == "ok" else status
        else:
            match = _direction_match(expected, actual)
        return {
            "name": "causal",
            "status": status,
            "direction": actual,
            "direction_match": match,
            "strength": min(1.0, abs(float(raw.get("normalized_ate", 0.0)))),
            "confidence": max(0.0, 1.0 - p_val),
            "p_value": p_val,
        }

    def _normalize_historical(
        self, raw: Dict[str, Any], resolved: ResolvedHypothesis
    ) -> Dict[str, Any]:
        status = raw.get("status", "insufficient_data")
        rate = float(raw.get("positive_rate", 0.0))
        avg_imp = float(raw.get("avg_improvement_pct", 0.0))
        if status != "ok":
            return {
                "name": "historical",
                "status": status,
                "direction": "neutral",
                "direction_match": None,
                "strength": 0.0,
                "confidence": 0.0,
            }
        direction = "positive" if rate >= 0.5 else "negative" if rate < 0.35 else "neutral"
        expected = resolved.expected_direction
        return {
            "name": "historical",
            "status": "ok",
            "direction": direction,
            "direction_match": _direction_match(expected, direction),
            "strength": min(1.0, abs(avg_imp) / 20.0),
            "confidence": min(1.0, raw.get("matches", 0) / 5.0),
            "positive_rate": rate,
        }

    def _normalize_shap(self, raw: Dict[str, Any], resolved: ResolvedHypothesis) -> Dict[str, Any]:
        status = raw.get("status", "skipped")
        aligned = bool(raw.get("aligned"))
        rank = raw.get("rank")
        strength = 0.0
        if aligned and rank:
            strength = max(0.2, 1.0 - (int(rank) - 1) / self.shap_top_n)
        return {
            "name": "shap",
            "status": status,
            "direction": "positive" if aligned else "neutral",
            "direction_match": True if aligned else None,
            "strength": strength,
            "confidence": 0.4 if aligned else 0.15,
            "rank": rank,
        }

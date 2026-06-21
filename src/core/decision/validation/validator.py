import pandas as pd
import numpy as np
import datetime
import threading
from typing import Dict, Any, List, Optional
import scipy.stats as stats

from src.core.sensitivity import SensitivityEngine
from src.core.forecaster import ProductForecaster
from src.core.simulator import ScenarioSimulator
from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("validation_engine")

class ValidationEngine:
    def __init__(
        self, 
        df_historical: Optional[pd.DataFrame],
        forecaster: ProductForecaster,
        sensitivity_engine: SensitivityEngine,
        simulator: ScenarioSimulator
    ):
        self._thread_local = threading.local()
        self._default_df = df_historical
        self.forecaster = forecaster
        self.sensitivity_engine = sensitivity_engine
        self.simulator = simulator
        cfg = load_decision_config()
        val_cfg = cfg.get("validation", {})
        self.forecast_horizon = val_cfg.get("forecast_horizon_days", 14)
        self.change_pct_default = val_cfg.get("change_pct_default", 10.0)
        self.change_pct_min = val_cfg.get("change_pct_min", 5.0)
        self.change_pct_max = val_cfg.get("change_pct_max", 25.0)
        self.causal_min_rows = val_cfg.get("causal_min_rows", 20)
        logger.info("Initialized ValidationEngine with parameters:")
        logger.info(f"  forecast_horizon={self.forecast_horizon} days")
        logger.info(f"  change_pct_default={self.change_pct_default}%")
        logger.info(f"  change_pct_bounds=[{self.change_pct_min}%, {self.change_pct_max}%]")
        logger.info(f"  causal_min_rows={self.causal_min_rows}")

    @property
    def df(self) -> Optional[pd.DataFrame]:
        if not hasattr(self._thread_local, "df"):
            return self._default_df
        return self._thread_local.df

    @df.setter
    def df(self, value: Optional[pd.DataFrame]):
        self._thread_local.df = value

    def run_correlation(self, kpi: str, driver: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Computes Pearson and Spearman correlation coefficients,
        plus Mutual Information score for non-linear relationship detection.
        """
        logger.info(f"run_correlation: Computing correlation for product_id={product_id}: driver={driver} -> KPI={kpi}")
        prod_data = self.df[self.df["product_id"] == product_id].copy()
        if len(prod_data) < 10 or kpi not in prod_data.columns or driver not in prod_data.columns:
            logger.warning(f"run_correlation: Insufficient rows ({len(prod_data)}) or missing columns ({driver}/{kpi}) for product_id={product_id}")
            return {"pearson": 0.0, "spearman": 0.0, "p_value": 1.0, "mi_score": 0.0}
            
        x = prod_data[driver].astype(float).values
        y = prod_data[kpi].astype(float).values
        
        # Pearson
        try:
            p_coef, p_val = stats.pearsonr(x, y)
            if np.isnan(p_coef) or pd.isna(p_coef): p_coef = 0.0
            if np.isnan(p_val) or pd.isna(p_val): p_val = 1.0
        except Exception as e:
            logger.error(f"run_correlation: Pearson correlation calculation failed: {e}")
            p_coef, p_val = 0.0, 1.0
            
        # Spearman
        try:
            s_coef, s_val = stats.spearmanr(x, y)
            if np.isnan(s_coef) or pd.isna(s_coef): s_coef = 0.0
            if np.isnan(s_val) or pd.isna(s_val): s_val = 1.0
        except Exception as e:
            logger.error(f"run_correlation: Spearman correlation calculation failed: {e}")
            s_coef, s_val = 0.0, 1.0

        # Mutual Information score (non-linear relationship detection)
        mi_score = 0.0
        try:
            from sklearn.feature_selection import mutual_info_regression
            mi_vals = mutual_info_regression(x.reshape(-1, 1), y, random_state=42)
            mi_score = round(float(mi_vals[0]), 4)
        except Exception as e:
            logger.error(f"run_correlation: Mutual Information calculation failed: {e}")
            mi_score = 0.0
            
        res = {
            "pearson": round(float(p_coef), 4),
            "spearman": round(float(s_coef), 4),
            "p_value": round(float(p_val), 4),
            "mi_score": mi_score
        }
        logger.info(f"run_correlation: Pearson={res['pearson']}, Spearman={res['spearman']}, p_value={res['p_value']}, MI={res['mi_score']}")
        return res

    def run_sensitivity_lookup(self, driver_key: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Queries the Sensitivity Engine to fetch elasticity scores and expected impact.
        """
        logger.info(f"run_sensitivity_lookup: Requesting sensitivity analysis for driver={driver_key} on product={product_id}")
        try:
            # Map hypothesis driver word to sensitivity keys
            driver_map = {
                "discount": "discount",
                "price": "price",
                "shipping": "shipping",
                "marketing": "marketing",
                "spend": "marketing",
                "inventory": "inventory",
                "return": "return",
                "retention": "return"
            }
            mapped_key = driver_map.get(driver_key.lower(), "discount")
            logger.debug(f"run_sensitivity_lookup: Mapped driver key to sensitivity lookup variable: '{mapped_key}'")
            
            sensitivity_results = self.sensitivity_engine.calculate_sensitivity(
                historical_df=self.df,
                product_id=product_id
            )
            res = sensitivity_results.get(mapped_key, {"elasticity_score": 0.0, "expected_impact": 0.0, "confidence": "Low"})
            logger.info(f"run_sensitivity_lookup: Elasticity={res.get('elasticity_score')}, Expected Impact={res.get('expected_impact')}, Confidence={res.get('confidence')}")
            return res
        except Exception as e:
            logger.error(f"run_sensitivity_lookup: Sensitivity calculation failed: {e}")
            return {
                "elasticity_score": 0.0,
                "expected_impact": 0.0,
                "confidence": "Low",
                "error": str(e)
            }

    def _compute_iqr_change_pct(self, driver_col: str, product_id: str) -> float:
        """
        Computes a data-driven change_pct from the driver column's IQR,
        bounded between config min/max. Falls back to config default on error.
        """
        logger.info(f"_compute_iqr_change_pct: Calculating data-driven perturbation delta from IQR for column: {driver_col}")
        try:
            prod_data = self.df[self.df["product_id"] == product_id]
            if len(prod_data) < 10 or driver_col not in prod_data.columns:
                logger.warning(f"_compute_iqr_change_pct: Insufficient data. Falling back to default={self.change_pct_default}%")
                return self.change_pct_default

            driver_vals = prod_data[driver_col].astype(float).dropna().values
            if len(driver_vals) < 10:
                logger.warning(f"_compute_iqr_change_pct: Insufficient data. Falling back to default={self.change_pct_default}%")
                return self.change_pct_default

            q75, q25 = np.percentile(driver_vals, [75, 25])
            median_val = np.median(driver_vals)

            if abs(median_val) < 1e-8:
                logger.warning(f"_compute_iqr_change_pct: Median value is zero. Falling back to default={self.change_pct_default}%")
                return self.change_pct_default

            change_pct = ((q75 - q25) / abs(median_val)) * 100.0
            clipped = float(np.clip(change_pct, self.change_pct_min, self.change_pct_max))
            logger.info(f"_compute_iqr_change_pct: Computed IQR change_pct={change_pct:.2f}% (Clipped to [{self.change_pct_min}%, {self.change_pct_max}%] -> {clipped:.2f}%)")
            return clipped
        except Exception as e:
            logger.error(f"_compute_iqr_change_pct: Failed computing IQR-based change percentage: {e}. Using default.")
            return self.change_pct_default

    def run_forecast_simulation(self, kpi: str, driver_col: str, change_pct: float, product_id: str = "P001") -> Dict[str, Any]:
        """
        Runs counterfactual forecasting simulation on the trained models.
        """
        logger.info(f"run_forecast_simulation: Simulating forecasting impact on KPI={kpi} from change_pct={change_pct:.2f}% on driver={driver_col}")
        try:
            # Get latest values for baseline comparison
            prod_data = self.df[self.df["product_id"] == product_id].copy()
            if prod_data.empty:
                logger.warning(f"run_forecast_simulation: Product data empty for product_id={product_id}")
                return {"baseline_forecast": 0.0, "simulated_forecast": 0.0, "delta_pct": 0.0}
                
            last_row = prod_data.iloc[-1]
            base_val = float(last_row[driver_col])
            raw_new_val = base_val * (1.0 + change_pct / 100.0) if base_val > 0 else (change_pct / 10.0)
            
            # Cast new_val to matching historical column dtype to avoid forecaster input type errors
            col_dtype = self.df[driver_col].dtype
            if np.issubdtype(col_dtype, np.integer):
                new_val = int(round(raw_new_val))
            else:
                new_val = float(raw_new_val)
            
            logger.debug(f"run_forecast_simulation: Baseline driver value={base_val}, Counterfactual perturbed value={new_val}")
            
            # Baseline forecast
            logger.debug(f"run_forecast_simulation: Triggering baseline forecaster prediction over {self.forecast_horizon} days horizon.")
            baseline = self.forecaster.forecast(
                historical_df=self.df,
                product_id=product_id,
                horizon_days=self.forecast_horizon
            )
            base_sum = float(baseline[kpi].sum()) if kpi in baseline.columns else float(baseline["revenue"].sum())
            
            # Perturbed counterfactual
            logger.debug(f"run_forecast_simulation: Triggering perturbed counterfactual prediction over {self.forecast_horizon} days horizon.")
            perturbed = self.forecaster.forecast(
                historical_df=self.df,
                product_id=product_id,
                horizon_days=self.forecast_horizon,
                current_features={driver_col: new_val}
            )
            sim_sum = float(perturbed[kpi].sum()) if kpi in perturbed.columns else float(perturbed["revenue"].sum())
            
            delta = sim_sum - base_sum
            pct = (delta / max(1.0, base_sum)) * 100.0
            
            res = {
                "baseline_forecast": round(base_sum, 2),
                "simulated_forecast": round(sim_sum, 2),
                "expected_delta": round(delta, 2),
                "delta_pct": round(pct, 2)
            }
            logger.info(f"run_forecast_simulation: Simulation completed. baseline={res['baseline_forecast']}, simulated={res['simulated_forecast']}, expected_delta={res['expected_delta']} ({res['delta_pct']}%)")
            return res
        except Exception as e:
            logger.error(f"run_forecast_simulation: Counterfactual forecasting failed: {e}")
            return {
                "baseline_forecast": 0.0,
                "simulated_forecast": 0.0,
                "expected_delta": 0.0,
                "delta_pct": 0.0,
                "error": str(e)
            }

    def run_causal_effect(self, kpi: str, driver: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Quantile-based tertile split ATE proxy (top 33% vs bottom 33%).
        Reduces noise from middle values compared to naive median split.
        Uses Welch's T-test for statistical significance.
        """
        logger.info(f"run_causal_effect: Running causal inference analysis for KPI={kpi}, driver={driver}")
        prod_data = self.df[self.df["product_id"] == product_id].copy()
        if len(prod_data) < self.causal_min_rows or kpi not in prod_data.columns or driver not in prod_data.columns:
            logger.warning(f"run_causal_effect: Insufficient historical rows ({len(prod_data)} < {self.causal_min_rows}) for causal Welch's T-test analysis.")
            return {"ate_estimate": 0.0, "p_value": 1.0, "is_pluggable_ready": True, "method": "Insufficient data"}
            
        driver_vals = prod_data[driver].astype(float).values
        kpi_vals = prod_data[kpi].astype(float).values

        # Tertile split: top 33% vs bottom 33%
        lower_bound = np.percentile(driver_vals, 33.3)
        upper_bound = np.percentile(driver_vals, 66.7)

        control = kpi_vals[driver_vals <= lower_bound]
        treatment = kpi_vals[driver_vals >= upper_bound]
        logger.debug(f"run_causal_effect: Quantile split - control size={len(control)} (driver <= {lower_bound:.2f}), treatment size={len(treatment)} (driver >= {upper_bound:.2f})")
        
        if len(treatment) < 5 or len(control) < 5:
            logger.warning("run_causal_effect: Subgroups are too small for Welch's T-Test (requires >= 5 per group).")
            return {"ate_estimate": 0.0, "p_value": 1.0, "is_pluggable_ready": True, "method": "Insufficient groups"}
            
        ate = np.mean(treatment) - np.mean(control)
        
        # Welch's T-test
        try:
            t_stat, p_val = stats.ttest_ind(treatment, control, equal_var=False)
            if np.isnan(p_val): p_val = 1.0
        except Exception as e:
            logger.error(f"run_causal_effect: Welch's T-test computation failed: {e}")
            p_val = 1.0
            
        res = {
            "ate_estimate": round(float(ate), 4),
            "p_value": round(float(p_val), 4),
            "is_pluggable_ready": True,
            "method": "ATE Proxy (Tertile Split: Top 33% vs Bottom 33%, Welch's T-Test)",
            "n_treatment": int(len(treatment)),
            "n_control": int(len(control))
        }
        logger.info(f"run_causal_effect: ATE Estimate={res['ate_estimate']}, p_value={res['p_value']} (Welch's T-Test)")
        return res

    def validate(
        self, 
        hypothesis: Dict[str, Any], 
        product_id: str = "P001",
        query_pcts: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full validation suite against a candidate hypothesis.
        Now uses IQR-based data-driven change_pct instead of fixed ±10%.
        """
        logger.info(f"validate: Commencing validation suite for hypothesis: '{hypothesis.get('hypothesis_id')}' - '{hypothesis.get('title')}'")
        original_df = self.df
        if self.df is None:
            logger.debug(f"validate: df_historical is None. Attempting to fetch from DB for product_id={product_id}")
            from src.api.dependencies import get_historical_df_from_db
            self.df = get_historical_df_from_db(product_id=product_id)
            
        try:
            hyp_id = hypothesis.get("hypothesis_id", "")
            affected_kpis = hypothesis.get("affected_kpis", ["total_revenue"])
            kpi = affected_kpis[0] if affected_kpis else "revenue"
            
            # Map internal Column Names
            kpi_col = "revenue" if "revenue" in kpi else "profit" if "profit" in kpi else "orders" if "orders" in kpi else "conversion_rate" if "conversion" in kpi else "revenue"
            
            # Map driver column based on hypothesis ID or keywords
            driver_col = "discount_pct"
            driver_key = "discount"
            if "shi" in hyp_id.lower() or "shipping" in hypothesis.get("title", "").lower():
                driver_col = "shipping_fee"
                driver_key = "shipping"
            elif "pri" in hyp_id.lower() or "price" in hypothesis.get("title", "").lower() or "pricing" in hypothesis.get("title", "").lower():
                driver_col = "avg_selling_price"
                driver_key = "price"
            elif "spend" in hypothesis.get("title", "").lower() or "marketing" in hypothesis.get("title", "").lower():
                driver_col = "marketing_spend"
                driver_key = "marketing"
                
            logger.info(f"validate: Mapped driver column={driver_col}, KPI column={kpi_col}")
            
            # 1. Run Correlation (now includes MI score)
            correlation = self.run_correlation(kpi_col, driver_col, product_id)
            
            # 2. Run Sensitivity
            sensitivity = self.run_sensitivity_lookup(driver_key, product_id)
            
            # 3. Run Forecast counterfactual — literal query shock or IQR-based data-driven change_pct
            if query_pcts and driver_col in query_pcts:
                change_pct = query_pcts[driver_col]
                logger.info(f"validate: Using parsed literal query shock change_pct={change_pct:.2f}% for driver={driver_col}")
            else:
                is_negative_change = "cut" in hypothesis.get("title", "").lower() or "reduce" in hypothesis.get("title", "").lower() or "drop" in hypothesis.get("title", "").lower() or "lower" in hypothesis.get("title", "").lower()
                change_pct = self._compute_iqr_change_pct(driver_col, product_id)
                if is_negative_change:
                    change_pct = -change_pct
                logger.info(f"validate: Calculated fallback IQR change_pct={change_pct:.2f}% for driver={driver_col}")
            
            forecast_sim = self.run_forecast_simulation(kpi_col, driver_col, change_pct, product_id)
            
            # 4. Run Causal Analysis (tertile split)
            causal = self.run_causal_effect(kpi_col, driver_col, product_id)
            
            logger.info(f"validate: Validation suite completed successfully for hypothesis '{hyp_id}'.")
            return {
                "correlation": correlation,
                "sensitivity": sensitivity,
                "forecast_simulation": forecast_sim,
                "causal": causal,
                "change_pct_used": change_pct,
                "validated_at": datetime.datetime.utcnow().isoformat()
            }
        finally:
            self.df = original_df

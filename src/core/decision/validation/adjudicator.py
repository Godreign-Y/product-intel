"""Family-aware hypothesis adjudication (Option B: model + historical sufficient)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.decision.config_loader import load_decision_config

SIGNAL_TO_FAMILY = {
    "forecast": "model_based",
    "sensitivity": "model_based",
    "shap": "model_based",
    "correlation": "historical",
    "causal": "historical",
    "historical": "empirical",
}

FAMILY_PRIORITY = ("model_based", "historical", "empirical")


def _vote_from_signal(signal: Dict[str, Any]) -> str:
    status = signal.get("status", "error")
    if status in ("insufficient_data", "error", "skipped"):
        return "inconclusive"
    if signal.get("direction_match") is True:
        return "agree"
    if signal.get("direction_match") is False:
        if signal.get("strength", 0) >= 0.2 and signal.get("confidence", 0) >= 0.4:
            return "disagree"
        return "inconclusive"
    return "inconclusive"


def _aggregate_family_vote(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not signals:
        return {"vote": "inconclusive", "driver_signal": None, "signals": []}

    scored = []
    for sig in signals:
        weight = float(sig.get("weight", 0.1))
        strength = float(sig.get("strength", 0))
        confidence = float(sig.get("confidence", 0))
        vote = _vote_from_signal(sig)
        score = weight * strength * confidence
        if vote == "agree":
            score += weight
        elif vote == "disagree":
            score -= weight
        scored.append((score, sig, vote))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_sig, best_vote = scored[0]

    if best_vote == "agree" and best_score > 0:
        family_vote = "agree"
    elif best_vote == "disagree" and best_score < 0:
        family_vote = "disagree"
    else:
        agrees = sum(1 for _, _, v in scored if v == "agree")
        disagrees = sum(1 for _, _, v in scored if v == "disagree")
        if agrees > disagrees and agrees > 0:
            family_vote = "agree"
        elif disagrees > agrees and disagrees > 0:
            family_vote = "disagree"
        else:
            family_vote = "inconclusive"

    return {
        "vote": family_vote,
        "driver_signal": best_sig.get("name"),
        "signals": [s.get("name") for s in signals],
    }


def adjudicate(
    signals: Dict[str, Dict[str, Any]],
    resolved: Any,
    plausibility: Dict[str, Any],
    multi_kpi_coherence: Dict[str, Any],
) -> Dict[str, Any]:
    cfg = load_decision_config()
    adj_cfg = cfg.get("validation", {}).get("adjudication", {})
    negligible = float(cfg.get("validation", {}).get("negligible_effect_pct", 2.0))

    families: Dict[str, Dict[str, Any]] = {}
    for family in FAMILY_PRIORITY:
        family_signals = [
            sig for name, sig in signals.items() if SIGNAL_TO_FAMILY.get(name) == family
        ]
        families[family] = _aggregate_family_vote(family_signals)

    agreeing = [f for f, data in families.items() if data["vote"] == "agree"]
    contradicting = [f for f, data in families.items() if data["vote"] == "disagree"]

    forecast = signals.get("forecast", {})
    primary_match = forecast.get("direction_match")
    primary_delta = abs(float(forecast.get("delta_pct", 0)))

    plaus_level = plausibility.get("level", "plausible")
    quality_flags: List[str] = list(plausibility.get("flags", []))
    if not multi_kpi_coherence.get("coherent", True):
        quality_flags.append("multi_kpi_unexpected_conflict")
    if forecast.get("status") == "ok" and primary_delta < negligible:
        quality_flags.append("negligible_forecast_effect")

    # Option B: supported needs >=2 agreeing families; model+historical counts without experiments
    verdict = "inconclusive"
    confidence_band = "low"

    model_vote = families["model_based"]["vote"]
    hist_vote = families["historical"]["vote"]
    emp_vote = families["empirical"]["vote"]

    if len(contradicting) >= int(adj_cfg.get("min_contradicting_families", 2)):
        verdict = "contradicted"
    elif model_vote == "disagree" and hist_vote == "disagree":
        verdict = "contradicted"
    elif (
        primary_match is False
        and primary_delta >= negligible
        and model_vote == "disagree"
    ):
        verdict = "contradicted"
    elif len(agreeing) >= int(adj_cfg.get("min_agreeing_families", 2)):
        if plaus_level == "implausible":
            verdict = "inconclusive"
            quality_flags.append("implausible_forecast_blocked_support")
        elif primary_match is False and primary_delta >= negligible:
            verdict = "inconclusive"
        elif model_vote == "disagree":
            verdict = "inconclusive"
        else:
            verdict = "supported"

    if verdict == "supported":
        if plaus_level == "unusual" or quality_flags:
            confidence_band = "medium"
        elif len(agreeing) >= 3 and not quality_flags:
            confidence_band = "high"
        else:
            confidence_band = "medium"
    elif verdict == "contradicted":
        confidence_band = "low"
    else:
        confidence_band = "low" if not agreeing else "medium"

    family_agreement = len(agreeing) / max(len(FAMILY_PRIORITY), 1)
    signal_votes = [_vote_from_signal(s) for s in signals.values() if s.get("status") == "ok"]
    signal_agreement = (
        signal_votes.count("agree") / len(signal_votes) if signal_votes else 0.0
    )

    summary = _build_summary(verdict, families, resolved, plaus_level)

    return {
        "verdict": verdict,
        "confidence_band": confidence_band,
        "family_agreement": round(family_agreement, 4),
        "signal_agreement": round(signal_agreement, 4),
        "supporting_families": agreeing,
        "contradicting_families": contradicting,
        "quality_flags": quality_flags,
        "summary": summary,
        "families": families,
    }


def _build_summary(
    verdict: str,
    families: Dict[str, Dict[str, Any]],
    resolved: Any,
    plaus_level: str,
) -> str:
    driver = getattr(resolved, "driver_col", "driver")
    kpi = getattr(resolved, "primary_kpi", "KPI")
    agreeing = [f for f, d in families.items() if d["vote"] == "agree"]
    if verdict == "supported":
        return (
            f"Hypothesis on {driver} affecting {kpi} is supported by "
            f"{len(agreeing)} independent evidence families ({', '.join(agreeing)}). "
            f"Plausibility: {plaus_level}."
        )
    if verdict == "contradicted":
        contra = [f for f, d in families.items() if d["vote"] == "disagree"]
        return (
            f"Hypothesis on {driver} affecting {kpi} is contradicted by "
            f"evidence families: {', '.join(contra) or 'model/historical signals'}."
        )
    return (
        f"Hypothesis on {driver} affecting {kpi} is inconclusive — "
        f"insufficient cross-family agreement for a firm validation."
    )


def verdict_rank_multiplier(verdict: str) -> float:
    cfg = load_decision_config()
    multipliers = cfg.get("validation", {}).get("adjudication", {}).get(
        "verdict_rank_multipliers",
        {"supported": 1.0, "inconclusive": 0.85, "contradicted": 0.50},
    )
    return float(multipliers.get(verdict, 0.85))

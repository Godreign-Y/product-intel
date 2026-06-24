"""Multi-KPI coherence checks for business-realistic trade-offs."""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.decision.config_loader import load_decision_config


def _delta_direction(delta_pct: float, negligible: float) -> str:
    if abs(delta_pct) < negligible:
        return "neutral"
    return "positive" if delta_pct > 0 else "negative"


def _expectation_matches(actual: str, expected: str) -> bool:
    if expected == "positive":
        return actual in ("positive", "neutral")
    if expected == "negative_or_mixed":
        return actual in ("negative", "neutral", "positive")
    if expected == "positive_or_mixed":
        return actual in ("positive", "neutral", "negative")
    return True


def check_multi_kpi_coherence(
    driver_col: str,
    kpi_deltas: Dict[str, float],
    negligible_effect_pct: float = 2.0,
) -> Dict[str, Any]:
    """
    Evaluate whether secondary KPI movements match economically expected patterns
    for the driver (e.g. discount up + orders up + profit down is coherent).
    """
    cfg = load_decision_config()
    expectations = cfg.get("validation", {}).get("cross_kpi_expectations", {}).get(
        driver_col, {}
    )

    details: Dict[str, Any] = {}
    unexpected: List[str] = []
    matched = 0
    checked = 0

    for kpi, delta in kpi_deltas.items():
        actual = _delta_direction(delta, negligible_effect_pct)
        expected = expectations.get(kpi, "positive_or_mixed")
        is_match = _expectation_matches(actual, expected)
        details[kpi] = {
            "delta_pct": round(float(delta), 2),
            "direction": actual,
            "expected": expected,
            "match": is_match,
        }
        if kpi in expectations:
            checked += 1
            if is_match:
                matched += 1
            else:
                unexpected.append(kpi)

    if not kpi_deltas:
        pattern = "no_data"
        coherent = True
    elif unexpected:
        pattern = "unexpected_conflict"
        coherent = False
    elif checked > 0 and matched == checked:
        pattern = "expected_trade_off" if len(kpi_deltas) > 1 else "aligned"
        coherent = True
    else:
        pattern = "aligned"
        coherent = True

    return {
        "coherent": coherent,
        "pattern": pattern,
        "unexpected_kpis": unexpected,
        "details": details,
    }

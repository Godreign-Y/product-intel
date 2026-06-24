"""Business plausibility sanity checks on forecast magnitudes."""

from __future__ import annotations

from typing import Any, Dict

from src.core.decision.config_loader import load_decision_config


def check_plausibility(
    driver_col: str,
    kpi_deltas: Dict[str, float],
) -> Dict[str, Any]:
    """
    Flag economically implausible forecast magnitudes per driver/KPI bounds.
    Does not veto hypotheses alone — downgrades confidence band downstream.
    """
    cfg = load_decision_config()
    bounds = cfg.get("validation", {}).get("plausibility_bounds", {}).get(driver_col, {})
    flags: list[str] = []
    level = "plausible"

    for kpi, delta in kpi_deltas.items():
        kpi_bounds = bounds.get(kpi)
        if not kpi_bounds:
            continue
        max_pos = float(kpi_bounds.get("max_positive", 999))
        max_neg = float(kpi_bounds.get("max_negative", 999))
        if delta > max_pos:
            flags.append(f"{kpi}_delta_{delta:.1f}_exceeds_max_positive_{max_pos}")
            level = "implausible"
        elif delta < -max_neg:
            flags.append(f"{kpi}_delta_{delta:.1f}_exceeds_max_negative_{max_neg}")
            level = "implausible"
        elif abs(delta) > max(max_pos, max_neg) * 0.6 and level != "implausible":
            flags.append(f"{kpi}_delta_{delta:.1f}_unusual")
            level = "unusual"

    return {
        "level": level,
        "flags": flags,
    }

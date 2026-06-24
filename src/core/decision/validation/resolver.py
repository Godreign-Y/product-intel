"""Canonical hypothesis resolution for the validation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.core.decision.config_loader import load_decision_config
from src.core.decision.direction_utils import parse_hypothesis_direction
from src.core.decision.normalization import normalize_driver, normalize_kpi

DRIVER_COL_TO_KEY: Dict[str, str] = {
    "discount_pct": "discount",
    "shipping_fee": "shipping",
    "avg_selling_price": "price",
    "marketing_spend": "marketing",
    "inventory_available": "inventory",
}

DEFAULT_DRIVERS = [
    "discount_pct",
    "shipping_fee",
    "avg_selling_price",
    "marketing_spend",
]


@dataclass
class ResolvedHypothesis:
    driver_col: str
    driver_key: str
    primary_kpi: str
    kpi_cols: List[str]
    expected_direction: str
    change_pct: float
    title: str


def kpi_to_column(kpi: str) -> str:
    k = normalize_kpi(kpi)
    if k in ("revenue", "profit", "orders", "conversion_rate", "retention_rate"):
        return k
    return "revenue"


def resolve_hypothesis(
    hypothesis: Dict[str, Any],
    df: Optional[pd.DataFrame],
    product_id: str,
    query_pcts: Optional[Dict[str, float]] = None,
) -> ResolvedHypothesis:
    """Resolve driver, KPIs, direction, and shock size from the hypothesis object."""
    cfg = load_decision_config()
    val_cfg = cfg.get("validation", {})
    min_deltas = cfg.get("elasticity", {}).get("min_driver_delta", {})

    title = hypothesis.get("title", "")
    driver_col = normalize_driver(hypothesis.get("driver_variable") or "")
    if driver_col not in DEFAULT_DRIVERS and driver_col not in min_deltas:
        driver_col = _fallback_driver_from_text(hypothesis)

    driver_key = DRIVER_COL_TO_KEY.get(driver_col, "discount")

    raw_kpis = hypothesis.get("affected_kpis") or ["revenue"]
    if isinstance(raw_kpis, str):
        raw_kpis = [raw_kpis]
    kpi_cols = [kpi_to_column(k) for k in raw_kpis if k]
    if not kpi_cols:
        kpi_cols = ["revenue"]
    primary_kpi = kpi_cols[0]

    expected_direction = parse_hypothesis_direction(title, driver_key)

    if query_pcts and driver_col in query_pcts:
        change_pct = float(query_pcts[driver_col])
    else:
        change_pct = _compute_change_pct(
            df=df,
            driver_col=driver_col,
            product_id=product_id,
            title=title,
            val_cfg=val_cfg,
            min_deltas=min_deltas,
        )

    return ResolvedHypothesis(
        driver_col=driver_col,
        driver_key=driver_key,
        primary_kpi=primary_kpi,
        kpi_cols=kpi_cols,
        expected_direction=expected_direction,
        change_pct=change_pct,
        title=title,
    )


def _fallback_driver_from_text(hypothesis: Dict[str, Any]) -> str:
    """Legacy fallback only when driver_variable is missing."""
    hyp_id = hypothesis.get("hypothesis_id", "").lower()
    title = hypothesis.get("title", "").lower()
    if "shi" in hyp_id or "shipping" in title:
        return "shipping_fee"
    if "pri" in hyp_id or "price" in title or "pricing" in title:
        return "avg_selling_price"
    if "spend" in title or "marketing" in title:
        return "marketing_spend"
    if "inventory" in title or "stock" in title:
        return "inventory_available"
    return "discount_pct"


def _compute_change_pct(
    df: Optional[pd.DataFrame],
    driver_col: str,
    product_id: str,
    title: str,
    val_cfg: Dict[str, Any],
    min_deltas: Dict[str, float],
) -> float:
    change_pct_default = float(val_cfg.get("change_pct_default", 10.0))
    change_pct_min = float(val_cfg.get("change_pct_min", 5.0))
    change_pct_max = float(val_cfg.get("change_pct_max", 25.0))

    change_pct = change_pct_default
    if df is not None and driver_col in df.columns:
        prod = df[df["product_id"] == product_id].copy()
        if "date" in prod.columns:
            prod["date"] = pd.to_datetime(prod["date"])
            prod = prod.sort_values("date")
        if len(prod) >= 10:
            vals = prod[driver_col].astype(float).dropna().values
            if len(vals) >= 10:
                q75, q25 = np.percentile(vals, [75, 25])
                median_val = np.median(vals)
                if abs(median_val) >= 1e-8:
                    change_pct = float(
                        np.clip(((q75 - q25) / abs(median_val)) * 100.0, change_pct_min, change_pct_max)
                    )

    min_delta = min_deltas.get(driver_col)
    if min_delta is not None and abs(change_pct) < abs(min_delta):
        change_pct = float(min_delta) if change_pct >= 0 else -float(min_delta)

    title_lower = title.lower()
    if any(w in title_lower for w in ("cut", "reduce", "drop", "lower", "decrease")):
        change_pct = -abs(change_pct)

    return change_pct


def get_product_frame(
    df: Optional[pd.DataFrame],
    product_id: str,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    prod = df[df["product_id"] == product_id].copy()
    if "date" in prod.columns:
        prod["date"] = pd.to_datetime(prod["date"])
        prod = prod.sort_values("date").reset_index(drop=True)
    return prod

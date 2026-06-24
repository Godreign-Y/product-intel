"""Unit tests for the upgraded ValidationEngine pipeline."""

import pandas as pd
import pytest
from unittest.mock import MagicMock

from src.core.decision.validation.resolver import resolve_hypothesis, kpi_to_column
from src.core.decision.validation.coherence import check_multi_kpi_coherence
from src.core.decision.validation.plausibility import check_plausibility
from src.core.decision.validation.adjudicator import adjudicate


def test_resolve_hypothesis_uses_driver_variable():
    hypo = {
        "title": "Budget cuts reduced revenue",
        "driver_variable": "marketing_spend",
        "affected_kpis": ["revenue"],
        "hypothesis_id": "HYP_MKT_01",
    }
    resolved = resolve_hypothesis(hypo, None, "P001", {"marketing_spend": -10.0})
    assert resolved.driver_col == "marketing_spend"
    assert resolved.driver_key == "marketing"
    assert resolved.change_pct == -10.0
    assert resolved.primary_kpi == "revenue"


def test_kpi_to_column_normalizes_aliases():
    assert kpi_to_column("total_revenue") == "revenue"
    assert kpi_to_column("mean_conversion_rate") == "conversion_rate"


def test_multi_kpi_coherence_expected_trade_off():
    result = check_multi_kpi_coherence(
        "discount_pct",
        {"orders": 12.0, "profit": -5.0},
        negligible_effect_pct=2.0,
    )
    assert result["coherent"] is True
    assert result["pattern"] in ("expected_trade_off", "aligned")


def test_plausibility_flags_implausible_magnitude():
    result = check_plausibility(
        "discount_pct",
        {"orders": -85.0},
    )
    assert result["level"] == "implausible"
    assert result["flags"]


def test_adjudicate_supported_model_plus_historical_option_b():
    resolved = MagicMock(driver_col="discount_pct", primary_kpi="orders", title="Discount increases orders")
    signals = {
        "forecast": {
            "name": "forecast",
            "status": "ok",
            "direction": "positive",
            "direction_match": True,
            "strength": 0.7,
            "confidence": 0.9,
            "weight": 0.35,
            "delta_pct": 8.0,
        },
        "sensitivity": {
            "name": "sensitivity",
            "status": "ok",
            "direction": "positive",
            "direction_match": True,
            "strength": 0.5,
            "confidence": 0.6,
            "weight": 0.25,
        },
        "correlation": {
            "name": "correlation",
            "status": "ok",
            "direction": "positive",
            "direction_match": True,
            "strength": 0.4,
            "confidence": 0.7,
            "weight": 0.10,
        },
        "causal": {
            "name": "causal",
            "status": "inconclusive",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.1,
            "confidence": 0.2,
            "weight": 0.10,
        },
        "historical": {
            "name": "historical",
            "status": "insufficient_data",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.0,
            "confidence": 0.0,
            "weight": 0.15,
        },
        "shap": {
            "name": "shap",
            "status": "skipped",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.0,
            "confidence": 0.0,
            "weight": 0.05,
        },
    }
    adj = adjudicate(
        signals,
        resolved,
        {"level": "plausible", "flags": []},
        {"coherent": True, "pattern": "aligned"},
    )
    assert adj["verdict"] == "supported"
    assert "model_based" in adj["supporting_families"]
    assert "historical" in adj["supporting_families"]


def test_adjudicate_model_only_is_inconclusive():
    resolved = MagicMock(driver_col="discount_pct", primary_kpi="orders", title="Discount increases orders")
    signals = {
        "forecast": {
            "name": "forecast",
            "status": "ok",
            "direction": "positive",
            "direction_match": True,
            "strength": 0.8,
            "confidence": 0.9,
            "weight": 0.35,
            "delta_pct": 10.0,
        },
        "sensitivity": {
            "name": "sensitivity",
            "status": "ok",
            "direction": "positive",
            "direction_match": True,
            "strength": 0.6,
            "confidence": 0.7,
            "weight": 0.25,
        },
        "correlation": {
            "name": "correlation",
            "status": "ok",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.1,
            "confidence": 0.2,
            "weight": 0.10,
        },
        "causal": {
            "name": "causal",
            "status": "inconclusive",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.0,
            "confidence": 0.0,
            "weight": 0.10,
        },
        "historical": {
            "name": "historical",
            "status": "insufficient_data",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.0,
            "confidence": 0.0,
            "weight": 0.15,
        },
        "shap": {
            "name": "shap",
            "status": "skipped",
            "direction": "neutral",
            "direction_match": None,
            "strength": 0.0,
            "confidence": 0.0,
            "weight": 0.05,
        },
    }
    adj = adjudicate(
        signals,
        resolved,
        {"level": "plausible", "flags": []},
        {"coherent": True, "pattern": "aligned"},
    )
    assert adj["verdict"] == "inconclusive"

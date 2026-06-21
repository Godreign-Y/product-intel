"""Tests for deterministic visualization builders."""

from src.core.agent.visualization.builder import build_from_step


def test_build_forecast_chart():
    data = {
        "product_id": "P001",
        "horizon_days": 7,
        "daily_details": [
            {"date": "2025-01-01", "revenue": 100.0, "orders": 5},
            {"date": "2025-01-02", "revenue": 120.0, "orders": 6},
        ],
    }
    charts = build_from_step("s1", "forecast_predict", data)
    assert len(charts) == 1
    assert charts[0]["chart_type"] == "line"
    assert charts[0]["data"]["labels"] == ["2025-01-01", "2025-01-02"]
    assert len(charts[0]["data"]["datasets"]) >= 1


def test_build_shap_chart():
    data = {
        "target_metric": "revenue",
        "date": "2025-01-05",
        "positive_drivers": [{"feature": "price", "clean_name": "Price", "shap_value": 0.4}],
        "negative_drivers": [{"feature": "competition", "clean_name": "Competition", "shap_value": -0.2}],
    }
    charts = build_from_step("s2", "explain_prediction", data)
    assert len(charts) == 1
    assert charts[0]["chart_type"] == "bar"
    assert charts[0]["index_axis"] == "y"


def test_build_nl2sql_bar_chart():
    data = {
        "row_count": 2,
        "columns": ["product_id", "total_revenue"],
        "rows": [
            {"product_id": "P001", "total_revenue": 500},
            {"product_id": "P002", "total_revenue": 300},
        ],
    }
    charts = build_from_step("s3", "nl2sql_query", data)
    assert len(charts) == 1
    assert charts[0]["chart_type"] == "bar"


def test_skips_error_payload():
    assert build_from_step("s1", "forecast_predict", {"error": "failed"}) == []

"""Tests for field resolver."""

from src.core.agent.field_resolver import resolve_field, resolve_from_prior_steps


def test_resolve_date_from_forecast_daily_details():
    data = {
        "product_id": "P001",
        "daily_details": [
            {"date": "2025-12-29", "revenue": 10},
            {"date": "2025-12-31", "revenue": 12},
        ],
    }
    assert resolve_field(data, "date") == "2025-12-31"


def test_resolve_from_prior_steps_prefers_latest():
    plan = [
        {"step_id": "s1", "tool_id": "nl2sql_query"},
        {"step_id": "s2", "tool_id": "forecast_predict"},
        {"step_id": "s3", "tool_id": "explain_prediction"},
    ]
    results = {
        "s1": {"rows": [{"product_id": "P001", "revenue": 50}]},
        "s2": {
            "daily_details": [{"date": "2025-12-31", "revenue": 100}],
        },
    }
    val = resolve_from_prior_steps(results, plan, "s3", "date")
    assert val == "2025-12-31"

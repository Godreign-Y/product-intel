"""Tests for agent result validator."""

from src.core.agent.nodes.validator import validate_results


def _state(plan, results, query="forecast and explain drivers for P001"):
    return {
        "execution_plan": plan,
        "step_results": results,
        "user_query": query,
    }


def test_validator_passes_partial_analytical_success():
    plan = [
        {"step_id": "s1", "tool_id": "forecast_predict"},
        {"step_id": "s2", "tool_id": "explain_prediction"},
    ]
    results = {
        "s1": {
            "product_id": "P001",
            "daily_details": [{"date": "2025-12-31", "revenue": 100.0}],
        },
        "s2": {"error": "Could not resolve input_from for ['date']."},
    }
    out = validate_results(_state(plan, results))
    assert out["validation_passed"] is True
    assert "partial results" in out["validation_notes"]


def test_validator_fails_when_no_usable_data():
    plan = [{"step_id": "s1", "tool_id": "explain_prediction"}]
    results = {"s1": {"error": "missing params"}}
    out = validate_results(_state(plan, results, query="why did revenue drop?"))
    assert out["validation_passed"] is False


def test_validator_passes_single_nl2sql_lookup():
    plan = [{"step_id": "s1", "tool_id": "nl2sql_query"}]
    results = {
        "s1": {
            "sql": "SELECT product_id, SUM(revenue) AS total_revenue FROM product_performance GROUP BY product_id ORDER BY total_revenue DESC LIMIT 5",
            "columns": ["product_id", "total_revenue"],
            "rows": [{"product_id": "P001", "total_revenue": 100}],
        }
    }
    out = validate_results(
        _state(plan, results, query="Show me the top 5 products by revenue")
    )
    assert out["validation_passed"] is True

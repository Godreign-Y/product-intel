from src.core.agent.field_resolver import resolve_field


def test_resolve_field_from_nl2sql_rows() -> None:
    result = {
        "rows": [{"product_id": "P002", "revenue": 100.0}],
        "columns": ["product_id", "revenue"],
    }
    assert resolve_field(result, "product_id") == "P002"


def test_resolve_field_from_anomaly_ranker() -> None:
    result = {
        "top_10_critical_products": [
            {"product_id": "P003", "severity_score": 88.0, "status": "critical"},
        ],
    }
    assert resolve_field(result, "product_id") == "P003"


def test_resolve_field_returns_none_on_error() -> None:
    assert resolve_field({"error": "failed"}, "product_id") is None

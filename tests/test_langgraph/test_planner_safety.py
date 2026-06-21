from src.core.agent.nodes.dag_planner import _normalize_dag


def test_normalize_replaces_placeholder_with_input_from() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "nl2sql_query",
            "params": {"query": "find top product"},
            "input_from": {},
            "depends_on": [],
        },
        {
            "step_id": "s2",
            "tool_id": "explain_prediction",
            "params": {"product_id": "P001", "target_metric": "revenue"},
            "input_from": {},
            "depends_on": ["s1"],
        },
    ]

    normalized = _normalize_dag(dag, "why did the top product drop?")

    assert "product_id" not in normalized[1]["params"]
    assert normalized[1]["input_from"]["product_id"] == {"step": "s1", "field": "product_id"}
    assert normalized[1]["input_from"]["date"] == {"step": "s1", "field": "date"}
    assert normalized[1]["depends_on"] == ["s1"]


def test_normalize_drops_unsupported_input_from_and_dependency() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "nl2sql_query",
            "params": {"query": "top products"},
            "input_from": {},
            "depends_on": [],
        },
        {
            "step_id": "s2",
            "tool_id": "anomaly_rank_products",
            "params": {"date": "2025-12-31", "kpi": "revenue"},
            "input_from": {"product_id": {"step": "s1", "field": "product_id"}},
            "depends_on": ["s1"],
        },
    ]

    normalized = _normalize_dag(dag, "rank anomalies for top products")

    assert normalized[1]["input_from"] == {}
    assert normalized[1]["depends_on"] == []

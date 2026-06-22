from src.core.agent.nodes.dag_planner import normalize_dag


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

    normalized = normalize_dag(dag, "why did the top product drop?")

    assert "product_id" not in normalized[1]["params"]
    assert normalized[1]["input_from"]["product_id"] == {"step": "s1", "field": "product_id"}
    assert "date" in normalized[1]["params"]
    assert "date" not in normalized[1]["input_from"]
    assert normalized[1]["depends_on"] == ["s1"]


def test_normalize_forces_input_from_after_discovery_nl2sql() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "nl2sql_query",
            "params": {"query": "Find the product_id and date with the largest revenue drop last week"},
            "input_from": {},
            "depends_on": [],
        },
        {
            "step_id": "s2",
            "tool_id": "explain_prediction",
            "params": {"product_id": "P001", "target_metric": "revenue", "date": "2025-11-25"},
            "input_from": {},
            "depends_on": ["s1"],
        },
    ]

    normalized = normalize_dag(
        dag,
        "Revenue for P001 dropped — explain why for the worst affected product",
    )

    assert "product_id" not in normalized[1]["params"]
    assert "date" not in normalized[1]["params"]
    assert normalized[1]["input_from"]["product_id"] == {"step": "s1", "field": "product_id"}
    assert normalized[1]["input_from"]["date"] == {"step": "s1", "field": "date"}


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

    normalized = normalize_dag(dag, "rank anomalies for top products")

    assert normalized[1]["input_from"] == {}
    assert normalized[1]["depends_on"] == []


def test_normalize_injects_explicit_product_and_date() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "explain_prediction",
            "params": {"target_metric": "revenue"},
            "input_from": {},
            "depends_on": [],
        },
    ]

    normalized = normalize_dag(dag, "Why did revenue drop for P001 on 2025-12-31?")

    assert len(normalized) == 1
    assert normalized[0]["params"]["product_id"] == "P001"
    assert normalized[0]["params"]["date"] == "2025-12-31"
    assert normalized[0]["input_from"] == {}


def test_normalize_replanner_keeps_date_from_query_not_nl2sql() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "nl2sql_query",
            "params": {"query": "Find the product_id for product P001"},
            "input_from": {},
            "depends_on": [],
        },
        {
            "step_id": "s2",
            "tool_id": "explain_prediction",
            "params": {"target_metric": "revenue"},
            "input_from": {
                "product_id": {"step": "s1", "field": "product_id"},
                "date": {"step": "s1", "field": "date"},
            },
            "depends_on": ["s1"],
        },
    ]

    normalized = normalize_dag(dag, "Why did revenue drop for P001 on 2025-12-31?")

    assert normalized[1]["params"]["product_id"] == "P001"
    assert normalized[1]["params"]["date"] == "2025-12-31"
    assert "date" not in normalized[1]["input_from"]
    assert "product_id" not in normalized[1]["input_from"]


def test_sanitize_strips_date_from_revenue_only_nl2sql() -> None:
    dag = [
        {
            "step_id": "s1",
            "tool_id": "nl2sql_query",
            "params": {
                "query": (
                    "SELECT product_id, revenue FROM product_performance "
                    "WHERE product_id = 'P001' AND date >= '2025-12-25'"
                ),
            },
            "input_from": {},
            "depends_on": [],
        },
        {
            "step_id": "s2",
            "tool_id": "forecast_predict",
            "params": {"horizon_days": 30, "product_id": "P001"},
            "input_from": {},
            "depends_on": ["s1"],
        },
        {
            "step_id": "s3",
            "tool_id": "explain_prediction",
            "params": {"target_metric": "revenue"},
            "input_from": {
                "product_id": {"step": "s1", "field": "product_id"},
                "date": {"step": "s1", "field": "date"},
            },
            "depends_on": ["s1", "s2"],
        },
    ]

    normalized = normalize_dag(
        dag,
        "Get recent revenue for P001, forecast next 30 days, and explain drivers",
    )

    assert "date" not in normalized[2]["input_from"] or normalized[2]["input_from"]["date"]["step"] == "s2"
    assert "date" in normalized[2]["params"] or normalized[2]["input_from"].get("date", {}).get("step") == "s2"

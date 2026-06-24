"""Tests for template-based heuristic DAG fallback."""

from src.core.agent.nodes.dag_planner import plan_dag
from src.core.agent.nodes.heuristic_planner import (
    build_heuristic_dag,
    extract_query_signals,
    select_heuristic_template,
)
from src.core.agent.state import AgentState


def test_heuristic_routes_channel_diagnosis_to_decision_chain() -> None:
    query = (
        "Our mobile app channel revenue has underperformed for 3 consecutive weeks — "
        "diagnose the root causes using available data and recommend a prioritized 3-step action plan."
    )
    dag = build_heuristic_dag(query, {})

    tool_ids = [step["tool_id"] for step in dag]
    assert tool_ids == ["analytics_channel", "analytics_trend", "decision_ask"]
    assert dag[-1]["params"]["query"] == query


def test_heuristic_forecast_explain_chain() -> None:
    query = "Forecast revenue for P002 for the next 30 days and explain the drivers."
    template = select_heuristic_template(extract_query_signals(query, {}))
    assert template == "forecast_explain_chain"

    dag = build_heuristic_dag(query, {})
    assert [s["tool_id"] for s in dag] == ["forecast_predict", "explain_prediction"]
    assert dag[0]["params"]["product_id"] == "P002"


def test_heuristic_simple_lookup_uses_nl2sql() -> None:
    dag = build_heuristic_dag("What is the total revenue?", {})
    assert len(dag) == 1
    assert dag[0]["tool_id"] == "nl2sql_query"
    assert dag[0]["params"]["query"] == "What is the total revenue?"
    assert not dag[0]["params"]["query"].lower().startswith("select")


def test_plan_dag_always_uses_llm_first(monkeypatch) -> None:
    """LLM planner is default; heuristic runs only when the LLM path fails."""
    llm_called = {"count": 0}

    class FakeLLM:
        def generate_compact(self, **kwargs):
            llm_called["count"] += 1
            return {
                "reasoning": "test",
                "dag": [
                    {
                        "step_id": "s1",
                        "tool_id": "analytics_kpi",
                        "params": {},
                        "input_from": {},
                        "depends_on": [],
                    }
                ],
            }

    query = (
        "Our mobile app channel revenue has underperformed for 3 consecutive weeks — "
        "diagnose the root causes and recommend a prioritized 3-step action plan."
    )
    state: AgentState = {
        "user_query": query,
        "extracted_params": {"query": query},
    }

    result = plan_dag(state, FakeLLM())
    assert llm_called["count"] == 1
    assert result["dag_source"] == "dynamic"
    assert result["execution_plan"][0]["tool_id"] == "analytics_kpi"


def test_replan_heuristic_rejects_nl2sql_only_for_complex_query() -> None:
    from src.core.agent.nodes.heuristic_planner import is_substantive_heuristic_plan

    query = "What is total revenue?"
    dag = build_heuristic_dag(query, {}, allow_nl2sql_only=False)
    assert not is_substantive_heuristic_plan(dag)


def test_replanner_prompt_format_escapes_jsonl_keys() -> None:
    from src.core.agent.nodes.replanner import _REPLANNER_SYSTEM_PROMPT

    rendered = _REPLANNER_SYSTEM_PROMPT.format(
        query="mobile channel",
        notes="failed",
        previous_dag="[]",
    )
    assert '"k":"r"' in rendered
    assert "mobile channel" in rendered

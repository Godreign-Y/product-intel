"""Tests for strict data_lookup gating in the intent classifier."""

from unittest.mock import MagicMock

from src.core.agent.nodes.intent_classifier import (
    _is_strict_data_lookup_query,
    classify_intent,
)
from src.core.agent.state import AgentState


def _state(query: str) -> AgentState:
    return {
        "user_query": query,
        "intent": "",
        "intent_confidence": 0.0,
        "extracted_params": {},
        "is_blocked": False,
        "block_reason": "",
        "dag_source": "",
        "execution_plan": [],
        "current_step_index": 0,
        "step_results": {},
        "execution_errors": [],
        "validation_passed": True,
        "validation_notes": "",
        "retry_count": 0,
        "final_response": "",
        "raw_data": {},
        "route_called": "",
    }


class TestStrictDataLookupPatterns:
    def test_accepts_clear_sql_lookup(self) -> None:
        assert _is_strict_data_lookup_query("What is the total revenue for P001 in January?")
        assert _is_strict_data_lookup_query("Show me the top 5 products by revenue last quarter")

    def test_rejects_forecast_queries(self) -> None:
        assert not _is_strict_data_lookup_query("What is the revenue forecast for P001 next month?")

    def test_rejects_explain_queries(self) -> None:
        assert not _is_strict_data_lookup_query(
            "What is the total revenue for P001 and why did it drop last week?"
        )

    def test_rejects_loose_revenue_phrasing(self) -> None:
        assert not _is_strict_data_lookup_query("What was revenue for P001 last month?")


class TestDataLookupRouting:
    def test_forecast_routes_to_analytical_not_nl2sql(self) -> None:
        mock_llm = MagicMock()
        result = classify_intent(_state("Forecast revenue for P001 over the next 45 days"), mock_llm)
        assert result["intent"] == "analytical"
        assert "execution_plan" not in result

    def test_llm_data_lookup_downgraded_without_strict_pattern(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "intent": "data_lookup",
            "confidence": 0.95,
            "extracted_params": {},
        }
        result = classify_intent(
            _state("Give me revenue breakdown for P001 by channel last month"),
            mock_llm,
        )
        assert result["intent"] == "analytical"
        assert "execution_plan" not in result

    def test_strict_total_query_fast_paths(self) -> None:
        mock_llm = MagicMock()
        result = classify_intent(_state("What is the total profit for P002 in Q1?"), mock_llm)
        assert result["intent"] == "data_lookup"
        assert result["dag_source"] == "regex_fast_path"
        assert result["execution_plan"][0]["tool_id"] == "nl2sql_query"
        mock_llm.generate_json.assert_not_called()

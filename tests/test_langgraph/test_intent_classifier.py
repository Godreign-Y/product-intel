"""
Tests for the Intent Classifier node.

Covers fast-path greetings, guardrail blocks, standard analytical
classification, and fallback behavior on LLM failure.
"""

import pytest
from unittest.mock import MagicMock

from src.core.agent.state import AgentState
from src.core.agent.nodes.intent_classifier import classify_intent, is_non_analytical


def _make_state(query: str) -> AgentState:
    """Create a minimal AgentState for testing."""
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
        "final_response": "",
        "raw_data": {},
        "route_called": "",
    }


class TestFastPathGreetings:
    """Test that common greetings bypass LLM entirely."""

    @pytest.mark.parametrize("query", ["hi", "hello", "hey", "yo", "hola"])
    def test_greeting_fast_path(self, query: str) -> None:
        mock_llm = MagicMock()
        state = _make_state(query)
        result = classify_intent(state, mock_llm)

        assert result["intent"] == "greeting"
        assert result["intent_confidence"] == 1.0
        assert result["is_blocked"] is False
        mock_llm.generate_json.assert_not_called()

    def test_short_query_fast_path(self) -> None:
        mock_llm = MagicMock()
        state = _make_state("ok")
        result = classify_intent(state, mock_llm)
        assert result["intent"] == "greeting"


class TestLLMClassification:
    """Test LLM-based classification for analytical queries."""

    def test_forecast_intent(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "intent": "forecast_request",
            "confidence": 0.95,
            "extracted_params": {"product_id": "P001", "horizon_days": 30},
        }
        state = _make_state("What is the revenue forecast for next month?")
        result = classify_intent(state, mock_llm)

        assert result["intent"] == "forecast_request"
        assert result["intent_confidence"] == 0.95
        assert result["is_blocked"] is False

    def test_out_of_scope_blocked(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "intent": "out_of_scope",
            "confidence": 0.9,
            "extracted_params": {},
        }
        state = _make_state("Write me a Python game")
        result = classify_intent(state, mock_llm)

        assert result["intent"] == "out_of_scope"
        assert result["is_blocked"] is True
        assert result["block_reason"] != ""


class TestLLMFailureFallback:
    """Test fallback when LLM classification fails."""

    def test_fallback_on_exception(self) -> None:
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("Connection timeout")
        state = _make_state("Show me the revenue trends with anomalies")
        result = classify_intent(state, mock_llm)

        assert result["intent"] == "multi_step_analysis"
        assert result["intent_confidence"] == 0.3


class TestIsNonAnalytical:
    """Test the helper function for routing decisions."""

    @pytest.mark.parametrize("intent", ["greeting", "system_status", "out_of_scope", "clarification_needed"])
    def test_non_analytical_intents(self, intent: str) -> None:
        state = _make_state("test")
        state["intent"] = intent
        assert is_non_analytical(state) is True

    @pytest.mark.parametrize("intent", ["forecast_request", "anomaly_check", "multi_step_analysis"])
    def test_analytical_intents(self, intent: str) -> None:
        state = _make_state("test")
        state["intent"] = intent
        assert is_non_analytical(state) is False

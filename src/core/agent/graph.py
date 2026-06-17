"""
LangGraph StateGraph — compiles and runs the agent pipeline.

Flow: Intent Classifier → (Fast Response | DAG Planner → DAG Executor → Synthesizer)
"""

from typing import Any

from langgraph.graph import StateGraph, END

from src.core.agent.state import AgentState
from src.core.agent.nodes.intent_classifier import classify_intent, is_non_analytical
from src.core.agent.nodes.dag_planner import plan_dag
from src.core.agent.nodes.dag_executor import execute_dag
from src.core.agent.nodes.synthesizer import (
    synthesize_fast_response,
    synthesize_analytical_response,
)
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("agent_graph")

# Module-level cache for compiled graph
_compiled_graph = None
_llm_client: LLMClient | None = None
_engines: dict[str, Any] = {}


def init_graph(llm_client: LLMClient, engines: dict[str, Any]) -> None:
    """Initialize the graph with shared resources. Called once at startup."""
    global _compiled_graph, _llm_client, _engines
    _llm_client = llm_client
    _engines = engines
    _compiled_graph = _build_graph()
    logger.info("LangGraph agent pipeline compiled successfully.")


def _build_graph() -> Any:
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    # ── Register nodes ───────────────────────────────────────────────
    graph.add_node("intent_classifier", _node_classify_intent)
    graph.add_node("fast_response", _node_fast_response)
    graph.add_node("dag_planner", _node_plan_dag)
    graph.add_node("dag_executor", _node_execute_dag)
    graph.add_node("synthesizer", _node_synthesize)

    # ── Set entry point ──────────────────────────────────────────────
    graph.set_entry_point("intent_classifier")

    # ── Conditional routing from intent classifier ───────────────────
    graph.add_conditional_edges(
        "intent_classifier",
        _route_after_classification,
        {
            "fast_response": "fast_response",
            "dag_planner": "dag_planner",
        },
    )

    # ── Linear edges ─────────────────────────────────────────────────
    graph.add_edge("fast_response", END)
    graph.add_edge("dag_planner", "dag_executor")
    graph.add_edge("dag_executor", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# ── Node wrappers (close over module-level client/engines) ───────────────


def _node_classify_intent(state: AgentState) -> dict[str, Any]:
    """Node wrapper for intent classification."""
    return classify_intent(state, _llm_client)


def _node_fast_response(state: AgentState) -> dict[str, Any]:
    """Node wrapper for fast non-analytical responses."""
    return synthesize_fast_response(state, _llm_client)


def _node_plan_dag(state: AgentState) -> dict[str, Any]:
    """Node wrapper for DAG planning."""
    return plan_dag(state, _llm_client)


def _node_execute_dag(state: AgentState) -> dict[str, Any]:
    """Node wrapper for DAG execution."""
    return execute_dag(state, _engines)


def _node_synthesize(state: AgentState) -> dict[str, Any]:
    """Node wrapper for report synthesis."""
    return synthesize_analytical_response(state, _llm_client)


# ── Routing functions ────────────────────────────────────────────────────


def _route_after_classification(state: AgentState) -> str:
    """Route to fast_response or dag_planner based on intent."""
    if is_non_analytical(state):
        return "fast_response"
    return "dag_planner"


# ── Public API ───────────────────────────────────────────────────────────


def run_agent_graph(query: str) -> dict[str, Any]:
    """Run a user query through the full LangGraph pipeline."""
    if _compiled_graph is None:
        raise RuntimeError("Agent graph not initialized. Call init_graph() first.")

    initial_state: AgentState = {
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

    result = _compiled_graph.invoke(initial_state)
    return result

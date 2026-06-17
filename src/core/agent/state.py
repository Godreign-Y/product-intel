"""
AgentState — shared state schema for the LangGraph pipeline.

Every node reads from and writes to this TypedDict as it flows
through the graph. This is the single source of truth.
"""

from typing import Any, TypedDict


class AgentState(TypedDict):
    """Shared state passed between all LangGraph nodes."""

    # ── Input ────────────────────────────────────────────────────────────
    user_query: str

    # ── Intent Classification ────────────────────────────────────────────
    intent: str
    intent_confidence: float
    extracted_params: dict[str, Any]

    # ── Guardrails ───────────────────────────────────────────────────────
    is_blocked: bool
    block_reason: str

    # ── Planning ─────────────────────────────────────────────────────────
    dag_source: str                        # "pre_compiled" | "dynamic"
    execution_plan: list[dict[str, Any]]   # ordered DAG steps

    # ── Execution ────────────────────────────────────────────────────────
    current_step_index: int
    step_results: dict[str, Any]           # {step_id: result_dict}
    execution_errors: list[str]

    # ── Output ───────────────────────────────────────────────────────────
    final_response: str
    raw_data: dict[str, Any]
    route_called: str                      # backward compat with API schema

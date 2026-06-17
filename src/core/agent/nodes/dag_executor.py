"""
DAG Executor Node — walks the execution plan step-by-step.

Iterates through the DAG, calls the appropriate tool node for each step,
accumulates results in step_results, and respects dependency ordering.
"""

from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.nodes.tool_nodes import execute_tool
from src.utils.logger import setup_logger

logger = setup_logger("dag_executor")


def execute_dag(state: AgentState, engines: dict[str, Any]) -> dict[str, Any]:
    """Execute all steps in the DAG plan sequentially."""
    plan = state["execution_plan"]
    step_results: dict[str, Any] = {}
    errors: list[str] = []
    last_tool_id = ""

    for step in plan:
        step_id = step.get("step_id", "unknown")
        tool_id = step.get("tool_id", "")
        params = dict(step.get("params", {}))

        # Ensure the raw user query is available in params for tools that need it
        if "query" not in params:
            params["query"] = state["user_query"]

        logger.info(f"Executing step {step_id}: {tool_id}")

        try:
            result = execute_tool(tool_id, params, engines)
            step_results[step_id] = result
            last_tool_id = tool_id
        except Exception as e:
            error_msg = f"Step {step_id} ({tool_id}) failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            step_results[step_id] = {"error": str(e)}

    # Build aggregated raw_data from the last successful step
    raw_data = step_results.get(plan[-1]["step_id"], {}) if plan else {}

    return {
        "step_results": step_results,
        "execution_errors": errors,
        "raw_data": raw_data,
        "route_called": last_tool_id,
        "current_step_index": len(plan),
    }

"""
DAG Executor Node — walks the execution plan step-by-step.

Iterates through the DAG, resolves temporal parameters, resolves data flow
from previous steps, calls the appropriate tool node for each step,
and accumulates results in step_results while respecting dependency ordering.
"""

from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.nodes.tool_nodes import execute_tool
from src.core.nl2sql.dates import resolve_date
from src.utils.logger import setup_logger

logger = setup_logger("dag_executor")

_DATE_PARAM_KEYS = {
    "date",
    "target_date",
    "start_date",
    "end_date",
    "period1_start",
    "period1_end",
    "period2_start",
    "period2_end",
}

_QUERY_PARAM_TOOLS = {"nl2sql_query", "decision_ask", "repository_search", "repository_extract"}


def execute_dag(state: AgentState, engines: dict[str, Any]) -> dict[str, Any]:
    """Execute all steps in the DAG plan sequentially."""
    plan = state.get("execution_plan", [])
    
    # Replanned DAGs are new plans. Reusing old step IDs like "s1" can skip the
    # corrected step and contaminate validation/synthesis with stale results.
    is_retry_plan = state.get("retry_count", 0) > 0
    step_results: dict[str, Any] = {} if is_retry_plan else dict(state.get("step_results", {}))
    
    # Track errors specifically for this execution run
    errors: list[str] = [] if is_retry_plan else list(state.get("execution_errors", []))
    last_tool_id = "" if is_retry_plan else state.get("route_called", "")

    for step in plan:
        step_id = step.get("step_id", "unknown")
        
        # If we're retrying and this step already succeeded previously, skip it
        if step_id in step_results and "error" not in step_results[step_id]:
            logger.info(f"Skipping already successful step {step_id}")
            continue

        tool_id = step.get("tool_id", "")
        params = dict(step.get("params", {}))
        input_from = step.get("input_from", {})
        depends_on = step.get("depends_on", [])

        # 1. Dependency Check
        deps_failed = False
        for dep in depends_on:
            if dep not in step_results:
                error_msg = f"Step {step_id} skipped: dependency {dep} not executed."
                logger.warning(error_msg)
                errors.append(error_msg)
                step_results[step_id] = {"error": error_msg}
                deps_failed = True
                break
            if "error" in step_results[dep]:
                error_msg = f"Step {step_id} skipped: dependency {dep} failed."
                logger.warning(error_msg)
                errors.append(error_msg)
                step_results[step_id] = {"error": error_msg}
                deps_failed = True
                break
                
        if deps_failed:
            continue

        # 2. Data Flow Resolution (input_from)
        for param_name, mapping in input_from.items():
            if isinstance(mapping, str):
                parts = mapping.split(".", 1)
                if len(parts) == 2:
                    source_step, source_field = parts[0], parts[1]
                else:
                    source_step, source_field = mapping, ""
            else:
                source_step = mapping.get("step")
                source_field = mapping.get("field")
            if source_step and source_field and source_step in step_results:
                source_data = step_results[source_step]
                
                # If it's a list (like rows from nl2sql), try to extract the field from the first item
                val = None
                if isinstance(source_data, dict):
                    if source_field in source_data:
                        val = source_data[source_field]
                    elif "rows" in source_data and isinstance(source_data["rows"], list) and len(source_data["rows"]) > 0:
                        val = source_data["rows"][0].get(source_field)
                
                if val is not None:
                    params[param_name] = val
                    logger.debug(f"Resolved input_from for {step_id}.{param_name} = {val} (from {source_step}.{source_field})")
                else:
                    logger.warning(f"Could not resolve input_from {source_step}.{source_field} for {step_id}.{param_name}")

        # 3. Temporal Resolution
        for k, v in params.items():
            if isinstance(v, str) and k in _DATE_PARAM_KEYS:
                # Attempt to parse as date. We don't overwrite if it fails parsing (might be a regular string)
                parsed_date = resolve_date(v)
                if parsed_date:
                    params[k] = parsed_date.strftime("%Y-%m-%d")

        # 4. Global fallback params
        if tool_id in _QUERY_PARAM_TOOLS and "query" not in params:
            params["query"] = state.get("user_query", "")

        # 4b. Enforce capability schema required parameters
        from src.core.agent.registry.capability_registry import CAPABILITY_REGISTRY
        schema = CAPABILITY_REGISTRY.get(tool_id, {}).get("input_schema", {})
        missing_required = []
        for param_name, spec in schema.items():
            if spec.get("required") and param_name not in params:
                missing_required.append(param_name)
        
        if missing_required:
            error_msg = f"Step {step_id} ({tool_id}) failed: Missing required parameters: {missing_required}. (Check if a previous step failed to output them)."
            logger.error(error_msg)
            errors.append(error_msg)
            step_results[step_id] = {"error": error_msg}
            continue

        # 5. Execute Tool
        logger.info(f"Executing step {step_id}: {tool_id} with params {params}")
        try:
            result = execute_tool(tool_id, params, engines)
            step_results[step_id] = result
            last_tool_id = tool_id
        except Exception as e:
            error_msg = f"Step {step_id} ({tool_id}) failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            step_results[step_id] = {"error": str(e)}

    # In multi-step, raw_data should contain all steps' results for the synthesizer
    # We assign step_results directly to raw_data so the synthesizer sees everything
    
    return {
        "step_results": step_results,
        "execution_errors": errors,
        "raw_data": step_results, 
        "route_called": last_tool_id,
        "current_step_index": len(plan),
    }

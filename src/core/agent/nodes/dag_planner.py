"""
DAG Planner Node — generates dynamic execution plans for complex queries.

Every analytical query goes through this node. It receives the full capability
registry, data registry, and temporal context to generate a robust multi-step DAG.
"""

from typing import TYPE_CHECKING, Any
import json

from src.core.agent.state import AgentState
from src.core.agent.prompts.planner_prompt import build_planner_system_prompt
from src.core.agent.registry.capability_registry import CAPABILITY_REGISTRY, get_tool_descriptions_for_prompt
from src.core.agent.registry.data_registry import get_data_summary_for_prompt
from src.core.nl2sql.dates import get_date_context_for_prompt
from src.utils.logger import setup_logger

if TYPE_CHECKING:
    from src.core.llm import LLMClient

logger = setup_logger("dag_planner")

_PLACEHOLDER_VALUES = {"P001", "2025-01-05"}
_DISCOVERABLE_FIELDS = {"product_id", "date", "target_date", "category"}


def plan_dag(state: AgentState, llm_client: "LLMClient") -> dict[str, Any]:
    """Generate a dynamic execution DAG using LLM with retry on failure."""
    logger.info("Generating dynamic DAG.")
    
    # Extract params that might have come from the fallback intent classifier
    extracted_params = state.get("extracted_params", {})
    query = state.get("user_query", "")
    if not query:
        query = extracted_params.get("query", "")
        
    tool_desc = get_tool_descriptions_for_prompt()
    data_desc = get_data_summary_for_prompt()
    temporal_context = get_date_context_for_prompt()
    params_json = json.dumps(extracted_params)

    system_prompt = build_planner_system_prompt(
        tool_descriptions=tool_desc,
        data_summary=data_desc,
        temporal_context=temporal_context,
        params_json=params_json
    )

    try:
        result = llm_client.generate_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        dag = _normalize_dag(result.get("dag", []), query)
        clarification = result.get("clarification", "")
        reasoning = result.get("reasoning", "")
        logger.info(f"Dynamic DAG generated with {len(dag)} steps.")
        logger.info(f"DAG Reasoning: {reasoning}")
        logger.info(f"Execution Plan:\n{json.dumps(dag, indent=2)}")
        if not dag:
            return {
                "dag_source": "dynamic_clarification",
                "execution_plan": [],
                "final_response": clarification or "I need one more detail to run this analysis. Which product, date range, or metric should I use?",
                "route_called": "clarification",
            }
        
        return {
            "dag_source": "dynamic",
            "execution_plan": dag,
        }

    except Exception as e:
        logger.error(f"Dynamic DAG generation failed: {e}. Retrying once...")
        try:
            # Simple retry mechanism
            error_feedback = f"Your previous attempt failed with error: {e}. Please ensure you output ONLY valid JSON matching the requested schema."
            result = llm_client.generate_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                    {"role": "user", "content": error_feedback},
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            dag = _normalize_dag(result.get("dag", []), query)
            clarification = result.get("clarification", "")
            logger.info(f"Dynamic DAG retry successful with {len(dag)} steps.")
            if not dag:
                return {
                    "dag_source": "dynamic_retry_clarification",
                    "execution_plan": [],
                    "final_response": clarification or "I need one more detail to run this analysis. Which product, date range, or metric should I use?",
                    "route_called": "clarification",
                }
            return {
                "dag_source": "dynamic_retry",
                "execution_plan": dag,
            }
        except Exception as retry_e:
            logger.error(f"Dynamic DAG retry also failed: {retry_e}. Using fallback.")
            return {
                "dag_source": "dynamic_fallback",
                "execution_plan": [
                    {
                        "step_id": "s1",
                        "tool_id": "analytics_kpi",
                        "params": {"query": query},
                        "depends_on": [],
                    }
                ],
            }


def _normalize_dag(dag: Any, query: str) -> list[dict[str, Any]]:
    """Make common LLM planning mistakes safer before execution."""
    if not isinstance(dag, list):
        return []

    normalized: list[dict[str, Any]] = []
    query_lower = query.lower()

    for raw_step in dag:
        if not isinstance(raw_step, dict):
            continue

        step = dict(raw_step)
        step_id = str(step.get("step_id") or f"s{len(normalized) + 1}")
        tool_id = step.get("tool_id", "")
        params = dict(step.get("params") or {})
        input_from = dict(step.get("input_from") or {})
        depends_on = list(step.get("depends_on") or [])

        spec = CAPABILITY_REGISTRY.get(tool_id, {})
        input_schema = spec.get("input_schema", {})
        allowed_params = set(input_schema)
        if allowed_params:
            params = {k: v for k, v in params.items() if k in allowed_params}
            input_from = {k: v for k, v in input_from.items() if k in allowed_params}

        previous_lookup = _latest_lookup_step(normalized)
        if previous_lookup:
            source_step, source_fields = previous_lookup
            for param_name, schema in input_schema.items():
                if param_name not in _DISCOVERABLE_FIELDS:
                    continue

                explicit_value = params.get(param_name)
                value_is_user_supplied = explicit_value and str(explicit_value).lower() in query_lower
                value_is_placeholder = explicit_value in _PLACEHOLDER_VALUES and not value_is_user_supplied
                value_is_missing_required = schema.get("required") and param_name not in params and param_name not in input_from

                if (value_is_placeholder or value_is_missing_required) and param_name in source_fields:
                    params.pop(param_name, None)
                    input_from[param_name] = {"step": source_step, "field": param_name}
                    if source_step not in depends_on:
                        depends_on.append(source_step)

        input_source_steps = {
            mapping.get("step")
            for mapping in input_from.values()
            if isinstance(mapping, dict) and mapping.get("step")
        }
        input_source_steps.update(
            mapping.split(".", 1)[0]
            for mapping in input_from.values()
            if isinstance(mapping, str) and mapping
        )
        if tool_id != "decision_ask":
            depends_on = [dep for dep in depends_on if dep in input_source_steps]

        step["step_id"] = step_id
        step["params"] = params
        step["input_from"] = input_from
        step["depends_on"] = depends_on
        normalized.append(step)

    return normalized


def _latest_lookup_step(steps: list[dict[str, Any]]) -> tuple[str, set[str]] | None:
    """Return the latest previous step that can expose tabular fields."""
    for step in reversed(steps):
        if step.get("tool_id") == "nl2sql_query":
            return str(step.get("step_id")), {"product_id", "date", "target_date", "category"}
        if step.get("tool_id") == "anomaly_rank_products":
            return str(step.get("step_id")), {"product_id", "date", "target_date"}
    return None

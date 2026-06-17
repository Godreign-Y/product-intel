"""
DAG Planner Node — generates dynamic execution plans for complex queries.

For standard intents, loads a pre-compiled DAG template (zero latency).
For novel/complex queries, calls the LLM to generate a custom DAG.
"""

from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.templates.standard_dags import STANDARD_DAGS
from src.core.agent.prompts.planner_prompt import build_planner_system_prompt
from src.core.agent.registry.capability_registry import get_tool_descriptions_for_prompt
from src.core.agent.registry.data_registry import get_data_summary_for_prompt
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("dag_planner")


def plan_dag(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Select a pre-compiled DAG or generate one dynamically."""
    intent = state["intent"]
    params = state["extracted_params"]

    # ── Pre-compiled DAG for standard intents ────────────────────────
    if intent in STANDARD_DAGS:
        template = STANDARD_DAGS[intent]
        plan = _hydrate_template(template, params)
        logger.info(f"Using pre-compiled DAG for intent '{intent}' ({len(plan)} steps)")
        return {
            "dag_source": "pre_compiled",
            "execution_plan": plan,
        }

    # ── Dynamic DAG generation via LLM ───────────────────────────────
    logger.info(f"No pre-compiled DAG for intent '{intent}'. Generating dynamically.")
    return _generate_dynamic_dag(state, llm_client)


def _hydrate_template(
    template: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fill a pre-compiled DAG template with extracted parameters."""
    hydrated: list[dict[str, Any]] = []
    for step in template:
        step_copy = {**step}
        # Merge extracted params into the step's params
        step_params = {**step_copy.get("params", {})}
        for key, val in params.items():
            if key in step_params or key not in step_params:
                step_params[key] = val
        step_copy["params"] = step_params
        hydrated.append(step_copy)
    return hydrated


def _generate_dynamic_dag(
    state: AgentState,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """Call the LLM to generate a custom execution DAG."""
    tool_desc = get_tool_descriptions_for_prompt()
    data_desc = get_data_summary_for_prompt()
    system_prompt = build_planner_system_prompt(tool_desc, data_desc)

    try:
        result = llm_client.generate_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": state["user_query"]},
            ],
            temperature=0.1,
            max_tokens=800,
        )
        dag = result.get("dag", [])
        logger.info(f"Dynamic DAG generated with {len(dag)} steps: {result.get('reasoning', '')}")
        return {
            "dag_source": "dynamic",
            "execution_plan": dag,
        }

    except Exception as e:
        logger.error(f"Dynamic DAG generation failed: {e}. Using single-step fallback.")
        return {
            "dag_source": "dynamic_fallback",
            "execution_plan": [
                {
                    "step_id": "s1",
                    "tool_id": "analytics_kpi",
                    "params": state["extracted_params"],
                    "depends_on": [],
                }
            ],
        }

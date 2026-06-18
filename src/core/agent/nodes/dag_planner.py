"""
DAG Planner Node — generates dynamic execution plans for complex queries.

Every analytical query goes through this node. It receives the full capability
registry, data registry, and temporal context to generate a robust multi-step DAG.
"""

from typing import Any
import json

from src.core.agent.state import AgentState
from src.core.agent.prompts.planner_prompt import build_planner_system_prompt
from src.core.agent.registry.capability_registry import get_tool_descriptions_for_prompt
from src.core.agent.registry.data_registry import get_data_summary_for_prompt
from src.core.nl2sql.dates import get_date_context_for_prompt
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("dag_planner")


def plan_dag(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
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
        dag = result.get("dag", [])
        reasoning = result.get("reasoning", "")
        logger.info(f"Dynamic DAG generated with {len(dag)} steps.")
        logger.info(f"DAG Reasoning: {reasoning}")
        logger.info(f"Execution Plan:\n{json.dumps(dag, indent=2)}")
        
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
            dag = result.get("dag", [])
            logger.info(f"Dynamic DAG retry successful with {len(dag)} steps.")
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

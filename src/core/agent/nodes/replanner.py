"""
Replanner Node — contextual re-planning after a validation failure.

Receives the original query, the failed DAG, and the specific validation notes.
Generates a new DAG, keeping successful steps intact where possible.
"""

from typing import Any
import json

from src.core.agent.state import AgentState
from src.core.agent.nodes.dag_planner import normalize_dag
from src.core.agent.registry.capability_registry import get_tool_descriptions_for_prompt
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("replanner")

_REPLANNER_SYSTEM_PROMPT = """\
You are the DAG Replanner. A previous execution plan failed.
Your job is to generate a NEW, corrected DAG that addresses the failure.

## CAPABILITIES
{tool_descriptions}

## CONTEXT
Original Query: "{query}"
Validation Failure Notes:
{notes}

Previous Failed DAG:
{previous_dag}

## INSTRUCTIONS
1. Analyze why the previous DAG failed (e.g. invalid params, missing data, incorrect tool).
2. Generate a NEW DAG. 
3. If the failure was due to missing data (like an empty NL2SQL result), try a different approach or different parameters (e.g. broaden the date range if applicable).
4. If a step previously succeeded, you may re-run it or skip it and just run the missing parts (but the safest is to generate the full corrected chain).
5. DO NOT invent or hallucinate parameter values. If a required parameter is not explicitly provided in the query, leave it out of 'params' entirely or map it using 'input_from' if it comes from a previous step's output. DO NOT use placeholder values like 'P001' unless explicitly requested.
6. Output format is exactly the same as the original planner.

## OUTPUT FORMAT
Respond with ONLY a JSON object. No text before or after.
{{
  "reasoning": "<why this new plan fixes the failure>",
  "dag": [
    {{
      "step_id": "s1",
      "tool_id": "<tool_id>",
      "params": {{ ... }},
      "input_from": {{}},
      "depends_on": []
    }}
  ]
}}
"""

def replan_dag(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Generate a corrected DAG after validation failure."""
    retry_count = state.get("retry_count", 0)
    
    if retry_count >= 1:
        logger.warning("Max retries reached. Forcing pass to synthesizer.")
        return {
            "validation_passed": True, # Force pass
            "validation_notes": state.get("validation_notes", "") + "\nMax retries reached."
        }
        
    logger.info("Validation failed. Initiating Replanner.")
    
    query = state.get("user_query", "")
    notes = state.get("validation_notes", "")
    previous_dag = json.dumps(state.get("execution_plan", []), indent=2)
    tool_desc = get_tool_descriptions_for_prompt()
    
    system_prompt = _REPLANNER_SYSTEM_PROMPT.format(
        tool_descriptions=tool_desc,
        query=query,
        notes=notes,
        previous_dag=previous_dag
    )

    try:
        result = llm_client.generate_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate the corrected DAG."}
            ],
            temperature=0.2,
            max_tokens=800,
            model_tier="capable"
        )
        new_dag = normalize_dag(
            result.get("dag", []),
            query,
            state.get("extracted_params"),
        )
        reasoning = result.get("reasoning", "")
        logger.info(f"Replanner generated new DAG with {len(new_dag)} steps.")
        logger.info(f"Replanner Reasoning: {reasoning}")
        logger.info(f"New Execution Plan:\n{json.dumps(new_dag, indent=2)}")

        return {
            "execution_plan": new_dag,
            "dag_source": "dynamic_retry",
            "retry_count": retry_count + 1,
            "validation_passed": False,
        }

    except Exception as e:
        logger.error(f"Replanner failed: {e}. Forcing pass to synthesizer.")
        return {
            "validation_passed": True,
            "validation_notes": notes + f"\nReplanner failed to generate fallback: {e}"
        }

"""
Replanner Node — contextual re-planning after a validation failure.

Order: deterministic wiring patch → LLM replan → heuristic template fallback.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.nodes.dag_planner import normalize_dag
from src.core.agent.nodes.heuristic_planner import (
    build_heuristic_dag,
    is_substantive_heuristic_plan,
)
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("replanner")

_WIRING_FAILURE = re.compile(
    r"Could not resolve input_from|Missing required parameters",
    re.I,
)

_REPLANNER_SYSTEM_PROMPT = """\
You are the DAG Replanner. A previous execution plan failed.
Generate a corrected minimal DAG.

Original Query: "{query}"
Failure: {notes}

Failed plan:
{previous_dag}

Rules:
- Fix only what failed. Keep successful tool choices when possible.
- Put explicit product_id/date from the user query directly in params — do NOT wire date from NL2SQL unless that step SELECTs date.
- For explain_prediction after forecast_predict, wire date from the forecast step or put the latest data date in params.
- Never invent placeholder values.
- You can generate multiple steps if needed.
- For diagnose/recommend/channel queries use analytics_channel + analytics_trend + decision_ask — NOT nl2sql alone.

Output JSONL only:
{{"k":"r","v":"..."}}
{{"k":"s","i":"s1","t":"tool_id","p":{{}},"f":{{}},"d":[]}}
"""


def try_heuristic_replan(state: AgentState) -> dict[str, Any] | None:
    """Last-resort template plan when the LLM replanner fails or returns nothing."""
    query = state.get("user_query", "")
    dag = build_heuristic_dag(
        query,
        state.get("extracted_params") or {},
        allow_nl2sql_only=False,
    )
    if not is_substantive_heuristic_plan(dag):
        return None

    logger.info("Heuristic replanner fallback (template match).")
    return {
        "execution_plan": dag,
        "dag_source": "heuristic_retry",
        "retry_count": state.get("retry_count", 0) + 1,
        "validation_passed": False,
    }


def try_deterministic_replan(state: AgentState) -> dict[str, Any] | None:
    """Patch common wiring failures without calling the LLM."""
    notes = state.get("validation_notes", "")
    if not _WIRING_FAILURE.search(notes):
        return None

    query = state.get("user_query", "")
    previous_plan = state.get("execution_plan", [])
    if not previous_plan:
        return None

    fixed_plan = normalize_dag(previous_plan, query, state.get("extracted_params"))
    if fixed_plan == previous_plan:
        return None

    logger.info("Deterministic replanner patched DAG without LLM.")
    return {
        "execution_plan": fixed_plan,
        "dag_source": "deterministic_retry",
        "retry_count": state.get("retry_count", 0) + 1,
        "validation_passed": False,
    }


def replan_dag(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Generate a corrected DAG after validation failure."""
    retry_count = state.get("retry_count", 0)

    if retry_count >= 1:
        logger.warning("Max retries reached. Forcing pass to synthesizer.")
        return {
            "validation_passed": True,
            "validation_notes": state.get("validation_notes", "") + "\nMax retries reached.",
        }

    logger.info("Validation failed. Initiating Replanner.")

    deterministic = try_deterministic_replan(state)
    if deterministic:
        logger.info(f"Patched plan:\n{json.dumps(deterministic['execution_plan'], indent=2)}")
        return deterministic

    query = state.get("user_query", "")
    notes = state.get("validation_notes", "")
    previous_dag = json.dumps(state.get("execution_plan", []), indent=2)

    try:
        system_prompt = _REPLANNER_SYSTEM_PROMPT.format(
            query=query,
            notes=notes,
            previous_dag=previous_dag,
        )
        result = llm_client.generate_compact(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Generate corrected DAG as JSONL."},
            ],
            parser="dag",
            temperature=0.1,
            max_tokens=400,
            model_tier="fast",
        )
        new_dag = normalize_dag(
            result.get("dag", []),
            query,
            state.get("extracted_params"),
        )
        reasoning = result.get("reasoning", "")
        logger.info(f"Replanner generated new DAG with {len(new_dag)} steps.")
        logger.info(f"Replanner Reasoning: {reasoning}")

        if new_dag:
            return {
                "execution_plan": new_dag,
                "dag_source": "dynamic_retry",
                "retry_count": retry_count + 1,
                "validation_passed": False,
            }

        logger.warning("LLM replanner returned an empty DAG. Trying heuristic fallback.")

    except Exception as e:
        logger.error(f"Replanner LLM failed: {e}. Trying heuristic fallback.")

    heuristic = try_heuristic_replan(state)
    if heuristic:
        logger.info(f"Heuristic replan:\n{json.dumps(heuristic['execution_plan'], indent=2)}")
        return heuristic

    logger.error("Replanner and heuristic fallback both failed. Forcing pass to synthesizer.")
    return {
        "validation_passed": True,
        "validation_notes": notes + "\nReplanner could not produce a corrected plan.",
    }

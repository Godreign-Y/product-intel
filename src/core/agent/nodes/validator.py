"""
Response Validator Node — deterministic checks plus compact LLM review on failure.
"""

from __future__ import annotations

import json
import re
from typing import Any

import numpy as np

from src.core.agent.state import AgentState
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("validator")

_encoder = None

_VALIDATOR_LLM_PROMPT = """\
You judge whether executed analytics steps adequately answer the user query.
Reply JSONL only (1-2 lines max):
{"ok":1}
or
{"ok":0,"notes":"short reason"}

ok=1 if results are usable even if incomplete. ok=0 only when the answer would mislead or is empty.
"""

_METRIC_TERMS: dict[str, tuple[str, ...]] = {
    "profit": ("profit", "profitable", "margin"),
    "revenue": ("revenue", "sales", "selling"),
    "orders": ("orders", "order volume", "units sold"),
    "conversion_rate": ("conversion", "conversion rate"),
    "retention_rate": ("retention", "retention rate"),
    "inventory_available": ("inventory", "stock"),
    "marketing_spend": ("marketing", "ad spend", "spend"),
}

_COMPLEX_QUERY_TOOL_HINTS: tuple[tuple[re.Pattern[str], tuple[str, ...], str], ...] = (
    (re.compile(r"\b(forecast|predict|projection|next|future)\b", re.I), ("forecast_predict",), "forecasting"),
    (re.compile(r"\b(why|explain|driver|cause|root cause|diagnos)\b", re.I), ("explain_prediction", "decision_ask"), "explanation/diagnosis"),
    (re.compile(r"\b(should we|recommend|recommendation|decision|strategy|actionable|action plan|prioritized)\b", re.I), ("decision_ask",), "decision recommendation"),
    (re.compile(r"\b(what if|what-if|simulate|simulation|scenario)\b", re.I), ("simulate_scenario", "decision_ask"), "scenario simulation"),
    (re.compile(r"\b(optimi[sz]e|maximi[sz]e|minimi[sz]e|best parameter|best discount|best price)\b", re.I), ("optimize_parameters",), "optimization"),
    (re.compile(r"\b(anomal|outlier|unusual|spike|drop)\b", re.I), ("anomaly_detect", "anomaly_rank_products", "explain_prediction", "decision_ask"), "anomaly/diagnosis"),
    (re.compile(r"\b(channel|mobile app)\b", re.I), ("analytics_channel", "decision_ask"), "channel analysis"),
)

_RANKING_TERMS = re.compile(r"\b(top|highest|lowest|most|least|biggest|smallest|best|worst)\b", re.I)
_AGGREGATE_TERMS = re.compile(r"\b(total|sum|average|avg|count|how many)\b", re.I)

_ANALYTICAL_RESULT_KEYS = frozenset({
    "daily_details", "positive_drivers", "negative_drivers", "kpis",
    "metrics_comparison", "ranked_products", "prediction_value",
    "explanation_summary", "optimized_forecast_sum", "baseline_forecast_sum",
    "channel_breakdown", "explanation", "ranked_hypotheses", "recommendations",
})


def _get_encoder() -> Any:
    global _encoder
    if _encoder is None:
        from src.core.history.embeddings.encoder import SentenceTransformerEncoder

        _encoder = SentenceTransformerEncoder()
    return _encoder


def _mentioned_metrics(query: str) -> list[str]:
    query_lower = query.lower()
    return [
        metric
        for metric, terms in _METRIC_TERMS.items()
        if any(term in query_lower for term in terms)
    ]


def _expected_complex_tools(query: str) -> tuple[list[str], list[str]]:
    expected_tools: list[str] = []
    reasons: list[str] = []
    for pattern, tools, reason in _COMPLEX_QUERY_TOOL_HINTS:
        if pattern.search(query):
            expected_tools.extend(tools)
            reasons.append(reason)
    return sorted(set(expected_tools)), reasons


def _text_blob(*parts: Any) -> str:
    return " ".join(str(part or "") for part in parts).lower()


def _executed_tools(plan: list[dict[str, Any]], step_results: dict[str, Any]) -> list[str]:
    tools: list[str] = []
    for step in plan:
        step_id = step.get("step_id")
        result = step_results.get(step_id)
        if isinstance(result, dict) and result and "error" not in result:
            tools.append(str(step.get("tool_id", "")))
    return tools


def _summarize_results(plan: list[dict[str, Any]], step_results: dict[str, Any]) -> str:
    parts: list[str] = []
    for step in plan:
        step_id = step.get("step_id")
        tool_id = step.get("tool_id")
        result = step_results.get(step_id)
        if not isinstance(result, dict):
            continue
        if result.get("error"):
            parts.append(f"{step_id}/{tool_id}:ERROR")
        elif result.get("rows"):
            parts.append(f"{step_id}/{tool_id}:{result.get('row_count', len(result['rows']))} rows")
        else:
            keys = [k for k in result.keys() if k not in ("sql", "query")][:6]
            parts.append(f"{step_id}/{tool_id}:{','.join(keys)}")
    return "; ".join(parts)[:800]


def _llm_validate(
    query: str,
    plan: list[dict[str, Any]],
    step_results: dict[str, Any],
    deterministic_notes: str,
    llm_client: LLMClient | None,
) -> tuple[bool | None, str]:
    if llm_client is None:
        return None, ""

    payload = {
        "query": query[:400],
        "planned_tools": [s.get("tool_id") for s in plan],
        "executed": _summarize_results(plan, step_results),
        "deterministic_notes": deterministic_notes[:500],
    }
    try:
        result = llm_client.generate_compact(
            messages=[
                {"role": "system", "content": _VALIDATOR_LLM_PROMPT},
                {"role": "user", "content": json.dumps(payload, default=str)},
            ],
            parser="validation",
            temperature=0.0,
            max_tokens=80,
            model_tier="fast",
        )
        ok = bool(result.get("ok", True))
        notes = str(result.get("notes", ""))
        logger.info("Validator LLM review: ok=%s notes=%s", ok, notes[:120])
        return ok, notes
    except Exception as e:
        logger.warning(f"Validator LLM review skipped: {e}")
        return None, ""


def _validate_single_nl2sql_result(query: str, result: Any) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "NL2SQL did not return a structured result."

    if result.get("error"):
        return False, f"NL2SQL failed: {result['error']}"

    sql = str(result.get("sql") or "")
    columns = result.get("columns") or []
    rows = result.get("rows") or []
    evidence = _text_blob(sql, " ".join(map(str, columns)), rows[:3])

    expected_tools, reasons = _expected_complex_tools(query)
    if expected_tools:
        return (
            False,
            "Query asks for "
            + ", ".join(reasons)
            + f"; NL2SQL alone is insufficient. Expected one of: {', '.join(expected_tools)}.",
        )

    missing_metrics = [metric for metric in _mentioned_metrics(query) if metric not in evidence]
    if missing_metrics:
        return False, "NL2SQL result is missing requested metric(s): " + ", ".join(missing_metrics)

    query_lower = query.lower()
    if "product" in query_lower and _RANKING_TERMS.search(query) and "product_id" not in evidence:
        return False, "Product ranking query did not return or group by product_id."

    if _RANKING_TERMS.search(query) and "order by" not in sql.lower():
        return False, "Ranking query SQL does not order the results."

    if _AGGREGATE_TERMS.search(query) and not re.search(r"\b(sum|avg|count|min|max)\s*\(", sql, re.I):
        return False, "Aggregate query SQL does not use an aggregate function."

    if not rows:
        return True, "Validation passed; NL2SQL returned no matching rows."

    return True, "Validation passed."


def _has_analytical_payload(result: Any) -> bool:
    if not isinstance(result, dict) or result.get("error"):
        return False
    if any(key in result for key in _ANALYTICAL_RESULT_KEYS):
        return True
    rows = result.get("rows")
    return isinstance(rows, list) and len(rows) > 0


def validate_results(state: AgentState, llm_client: LLMClient | None = None) -> dict[str, Any]:
    """Validate step results for completeness, non-emptiness, and relevance."""
    plan = state.get("execution_plan", [])
    step_results = state.get("step_results", {})
    query = state.get("user_query", "")

    notes: list[str] = []
    passed = True

    if not plan:
        return {"validation_passed": False, "validation_notes": "No execution plan was produced."}

    if len(plan) == 1 and plan[0].get("tool_id") == "nl2sql_query":
        step_id = plan[0].get("step_id")
        result = step_results.get(step_id)
        if result is None:
            return {
                "validation_passed": False,
                "validation_notes": f"Step {step_id} did not produce a result.",
            }

        nl2sql_passed, nl2sql_notes = _validate_single_nl2sql_result(query, result)
        if not nl2sql_passed:
            llm_ok, llm_notes = _llm_validate(query, plan, step_results, nl2sql_notes, llm_client)
            if llm_ok is True:
                return {"validation_passed": True, "validation_notes": llm_notes or nl2sql_notes}
            logger.warning(f"Single-step NL2SQL validation failed: {nl2sql_notes}")
            return {"validation_passed": False, "validation_notes": nl2sql_notes}

        return {"validation_passed": True, "validation_notes": nl2sql_notes}

    planned_tools = [step.get("tool_id", "") for step in plan]
    executed = _executed_tools(plan, step_results)
    expected_tools, reasons = _expected_complex_tools(query)

    if expected_tools and not any(tool in expected_tools for tool in executed):
        passed = False
        notes.append(
            "Results missing required analysis: query asks for "
            + ", ".join(reasons)
            + f" but none of {', '.join(expected_tools)} succeeded."
        )

    executed_count = sum(
        1 for step in plan
        if step.get("step_id") in step_results
        and "error" not in (step_results.get(step.get("step_id")) or {})
    )
    if executed_count < len(plan):
        passed = False
        notes.append(f"Incomplete execution: {executed_count}/{len(plan)} steps succeeded.")

    has_valid_data = False
    analytical_successes = 0
    step_errors = 0
    for step in plan:
        step_id = step.get("step_id")
        result = step_results.get(step_id)
        if not result or result == {}:
            notes.append(f"Step {step_id} returned empty result.")
        elif "error" in result:
            step_errors += 1
            notes.append(f"Step {step_id} failed: {result['error']}")
        elif "rows" in result and len(result["rows"]) == 0:
            notes.append(f"Step {step_id} executed but found 0 records.")
        else:
            has_valid_data = True
            if _has_analytical_payload(result):
                analytical_successes += 1

    if not has_valid_data:
        passed = False
        notes.append("No valid data was produced by any step.")
    elif step_errors > 0 and analytical_successes > 0:
        notes.append(
            f"{step_errors} step(s) failed but {analytical_successes} step(s) produced usable data."
        )
    elif step_errors > 0:
        passed = False

    final_notes = "\n".join(notes) if notes else "Validation passed."

    if not passed and llm_client is not None:
        llm_ok, llm_notes = _llm_validate(query, plan, step_results, final_notes, llm_client)
        if llm_ok is True:
            passed = True
            final_notes = llm_notes or final_notes + "\n(LLM review: acceptable partial results.)"
        elif llm_ok is False and llm_notes:
            final_notes = final_notes + "\nLLM review: " + llm_notes

    if not passed:
        logger.warning(f"Validation failed:\n{final_notes}")
    else:
        logger.info("Validation passed.")

    logger.info(f"--- VALIDATION RESULT ---\nPassed: {passed}\nNotes: {final_notes}\n-------------------------")

    return {
        "validation_passed": passed,
        "validation_notes": final_notes,
    }

"""
Synthesizer Node — final LLM call to produce a natural language report.

Handles both non-analytical fast responses (greetings, meta queries, blocks) and
full analytical synthesis from accumulated DAG step results.
"""

import json
from typing import Any

from src.core.agent.state import AgentState
from src.core.agent.registry.capability_registry import get_tool_descriptions_for_prompt
from src.core.agent.registry.data_registry import get_data_summary_for_prompt
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("synthesizer")

_SYNTHESIS_SYSTEM_PROMPT = """\
You are a professional Business Intelligence Assistant.
The user asked a question. An analytics engine ran calculations and produced raw JSON data.
Summarize the results clearly in natural language using professional markdown.
Highlight the most critical business insights and recommendations.
Do not reference internal technical details like step IDs (e.g. 's1', 's2') or raw JSON keys.
Speak directly to the business user."""


def synthesize_fast_response(state: AgentState, llm_client: LLMClient) -> dict[str, Any]:
    """Generate a fast response for non-analytical intents."""
    intent = state["intent"]

    if intent == "greeting":
        return {
            "final_response": (
                "Hello! I'm your AI-powered Business Analytics Assistant. "
                "I can help you with forecasting, trend analysis, anomaly detection, "
                "what-if simulations, and strategic recommendations. How can I assist you today?"
            ),
            "raw_data": {},
            "route_called": "greeting",
        }

    if intent == "system_status":
        return {
            "final_response": "The system is online and healthy. All analytics engines are operational.",
            "raw_data": {"status": "healthy"},
            "route_called": "system_status",
        }

    if intent == "meta_query":
        tools_str = get_tool_descriptions_for_prompt()
        data_str = get_data_summary_for_prompt()
        return {
            "final_response": "",
            "raw_data": {"tools_str": tools_str, "data_str": data_str},
            "route_called": "meta_query",
        }

    if state.get("is_blocked"):
        return {
            "final_response": (
                "I'm sorry, but I can only help with business analytics questions. "
                "Try asking about forecasts, trends, anomalies, or strategic recommendations."
            ),
            "raw_data": {},
            "route_called": "guardrail_block",
        }

    # clarification_needed or unknown
    return {
        "final_response": (
            "Could you please provide more details? For example, you can ask me to "
            "forecast revenue, explain why a metric changed, simulate a what-if scenario, "
            "or recommend an optimal pricing strategy."
        ),
        "raw_data": {},
        "route_called": "clarification",
    }


def synthesize_analytical_response_stream(
    state: AgentState,
    llm_client: LLMClient,
):
    """Synthesize a natural language report from analytical results, yielding text stream."""
    raw_data = state.get("raw_data", {})
    route = state.get("route_called", "")
    notes = state.get("validation_notes", "")

    # For a 1-step DAG where the only step is nl2sql_query, we can fast-path formatting
    if route == "nl2sql_query" and len(state.get("execution_plan", [])) == 1:
        step_id = state["execution_plan"][0]["step_id"]
        step_data = raw_data.get(step_id, raw_data)
        
        formatted = _format_nl2sql_response(state.get("user_query", ""), step_data)
        if formatted is not None:
            if notes and "passed" not in notes.lower():
                formatted += f"\n\n> **Note:** {notes}"
            yield formatted
            return

    # If the decision engine already produced an explanation in the final step, use it
    if route == "decision_ask":
        for val in raw_data.values():
            if isinstance(val, dict) and "explanation" in val:
                resp = val["explanation"]
                if notes and "passed" not in notes.lower():
                    resp += f"\n\n> **Note:** {notes}"
                yield resp
                return

    # Handle Meta Query Streaming
    if route == "meta_query":
        query = state.get("user_query", "What can you do?")
        tools_str = raw_data.get("tools_str", "")
        data_str = raw_data.get("data_str", "")
        system_msg = (
            "You are a helpful Business Intelligence AI. The user is asking about your capabilities or data access. "
            f"Here is the list of your capabilities:\n\n{tools_str}\n\n"
            f"Here is the available data context:\n\n{data_str}\n\n"
            "Answer the user's specific query concisely and professionally based ONLY on these capabilities and data context."
        )
        try:
            yield from llm_client.generate_stream(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": query},
                ],
                temperature=0.2,
                max_tokens=600,
                model_tier="fast"
            )
        except Exception as e:
            logger.error(f"Meta query synthesis failed: {e}")
            yield "Here is an overview of my capabilities. You can ask me to forecast revenue, explain metric drops, simulate business scenarios, or recommend pricing and marketing strategies."
        return

    # Generic LLM synthesis for single or multi-step results
    try:
        truncated = json.dumps(raw_data, indent=2, default=str)[:4000]
        user_msg = f'User Query: "{state["user_query"]}"\n'
        if notes and "passed" not in notes.lower():
            user_msg += f'Validation Context (Mention to user if relevant): "{notes}"\n'
        user_msg += f"Raw Data Results (from DAG execution):\n{truncated}"

        yield from llm_client.generate_stream(
            messages=[
                {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=800,
            model_tier="fast", # Use fast model for synthesis
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        yield (
            f"Analysis completed. Here are the raw results:\n\n"
            f"{json.dumps(raw_data, indent=2, default=str)[:2000]}"
        )


def _format_nl2sql_response(question: str, raw_data: dict[str, Any]) -> str | None:
    """Build a markdown answer directly from NL2SQL tabular results."""
    if not isinstance(raw_data, dict):
        return None
        
    if raw_data.get("error"):
        return (
            "I couldn't retrieve that from the database. "
            f"Reason: {raw_data['error']}\n\n"
            "Try rephrasing, or specify a product (e.g. P001) and a date range."
        )

    rows = raw_data.get("rows", [])
    if not rows:
        return "No matching records were found for that query."

    columns = raw_data.get("columns") or list(rows[0].keys())

    lines: list[str] = []
    if question:
        lines.append(f"Here are the results for: _{question.strip()}_\n")

    lines.append("| " + " | ".join(str(c) for c in columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")

    for row in rows:
        cells = []
        for col in columns:
            val = row.get(col)
            if val is None:
                cells.append("—")
            elif isinstance(val, float):
                cells.append(f"{val:,.2f}")
            elif isinstance(val, int):
                cells.append(f"{val:,}")
            else:
                cells.append(str(val))
        lines.append("| " + " | ".join(cells) + " |")

    lines.append(f"\n**{len(rows)} row(s) returned.**")
    if raw_data.get("truncated"):
        lines.append("_Showing the first 100 rows._")

    return "\n".join(lines)

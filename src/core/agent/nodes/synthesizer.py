"""
Synthesizer Node — final LLM call to produce a natural language report.

Handles both non-analytical fast responses (greetings, blocks) and
full analytical synthesis from accumulated step results.
"""

import json
from typing import Any

from src.core.agent.state import AgentState
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("synthesizer")

_SYNTHESIS_SYSTEM_PROMPT = """\
You are a professional Business Intelligence Assistant.
The user asked a question. An analytics engine ran calculations and produced raw JSON data.
Summarize the results clearly in natural language using professional markdown.
Highlight the most critical business insights and recommendations.
Do not reference internal technical details like route names or raw JSON keys.
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

    if state.get("is_blocked"):
        return {
            "final_response": (
                "I'm sorry, but I can only help with business analytics questions. "
                "Try asking about forecasts, trends, anomalies, or strategic recommendations."
            ),
            "raw_data": {},
            "route_called": "guardrail_block",
        }

    # clarification_needed
    return {
        "final_response": (
            "Could you please provide more details? For example, you can ask me to "
            "forecast revenue, explain why a metric changed, simulate a what-if scenario, "
            "or recommend an optimal pricing strategy."
        ),
        "raw_data": {},
        "route_called": "clarification",
    }


def synthesize_analytical_response(
    state: AgentState,
    llm_client: LLMClient,
) -> dict[str, Any]:
    """Synthesize a natural language report from analytical results."""
    raw_data = state.get("raw_data", {})
    route = state.get("route_called", "")

    # If the decision engine already produced an explanation, use it directly
    if route == "decision_ask" and "explanation" in raw_data:
        return {"final_response": raw_data["explanation"]}

    # NL2SQL: format tabular results deterministically (fast, no truncation)
    if route == "nl2sql_query":
        formatted = _format_nl2sql_response(state.get("user_query", ""), raw_data)
        if formatted is not None:
            return {"final_response": formatted}

    # LLM synthesis
    try:
        truncated = json.dumps(raw_data, indent=2, default=str)[:3000]
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f'User Query: "{state["user_query"]}"\n'
                        f'Executed Action: "{route}"\n'
                        f"Raw Data Result:\n{truncated}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=600,
        )
        return {"final_response": response}

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {
            "final_response": (
                f"Analysis completed successfully. Here are the raw results:\n\n"
                f"{json.dumps(raw_data, indent=2, default=str)[:2000]}"
            ),
        }


def _format_nl2sql_response(question: str, raw_data: dict[str, Any]) -> str | None:
    """Build a markdown answer directly from NL2SQL tabular results."""
    if raw_data.get("error"):
        return (
            "I couldn't retrieve that from the database. "
            f"Reason: {raw_data['error']}\n\n"
            "Try rephrasing, or specify a product (e.g. P001) and a date range "
            "within 2025-01-01 to 2025-12-31."
        )

    rows = raw_data.get("rows", [])
    if not rows:
        return (
            "No matching records were found for that query. "
            "Note: the available data covers 2025-01-01 to 2025-12-31."
        )

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

"""
LLM visualization planner — selects and titles charts from deterministic candidates.
"""

from __future__ import annotations

import json
from typing import Any

from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("viz_planner")

_SKIP_ROUTES = frozenset({
    "greeting", "system_status", "guardrail_block", "clarification", "meta_query", "",
})

_PLANNER_PROMPT = """\
You are a data visualization director for a premium analytics product.
Given the user query and candidate chart definitions (with data already mapped), select the best 0–4 charts.

Rules:
- Keep charts that directly help answer the query. Drop redundant or weak candidates.
- Rewrite title/subtitle to be concise and executive-friendly (max 6 words title).
- Never invent data or chart types not in the candidate list.
- Return empty list if data is irrelevant to the query or candidates are weak.
- Prefer SHAP driver charts for "why" questions, forecasts for projection questions, comparisons for period questions.

Output ONLY JSON:
{
  "visualizations": [
    {
      "id": "<candidate id>",
      "title": "...",
      "subtitle": "...",
      "rationale": "one short sentence"
    }
  ]
}
"""


def plan_visualizations(
    query: str,
    route_called: str,
    intent: str,
    candidates: list[dict[str, Any]],
    llm_client: LLMClient,
) -> list[dict[str, Any]]:
    if route_called in _SKIP_ROUTES or intent in _SKIP_ROUTES:
        return []
    if not candidates:
        return []

    if len(candidates) <= 2:
        return candidates

    summary = [
        {
            "id": c["id"],
            "chart_type": c["chart_type"],
            "title": c["title"],
            "subtitle": c.get("subtitle", ""),
            "source_tool": c.get("source_tool", ""),
        }
        for c in candidates
    ]

    try:
        result = llm_client.generate_json(
            messages=[
                {"role": "system", "content": _PLANNER_PROMPT},
                {"role": "user", "content": json.dumps({"query": query, "candidates": summary}, indent=2)},
            ],
            temperature=0.1,
            max_tokens=500,
            model_tier="fast",
        )
        selected = result.get("visualizations") or []
        by_id = {c["id"]: c for c in candidates}
        merged: list[dict[str, Any]] = []
        for item in selected[:4]:
            viz_id = item.get("id")
            if viz_id not in by_id:
                continue
            chart = dict(by_id[viz_id])
            if item.get("title"):
                chart["title"] = item["title"]
            if item.get("subtitle"):
                chart["subtitle"] = item["subtitle"]
            chart["rationale"] = item.get("rationale", "")
            merged.append(chart)
        if merged:
            return merged
    except Exception as e:
        logger.warning(f"Viz LLM planner failed, using top candidates: {e}")

    return candidates[:3]

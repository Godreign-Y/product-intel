"""
Visualization generator — discovers charts, plans with LLM, streams build events.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterator

from src.core.agent.state import AgentState
from src.core.agent.visualization.builder import build_from_step
from src.core.agent.visualization.planner import plan_visualizations
from src.core.llm import LLMClient
from src.utils.logger import setup_logger

logger = setup_logger("viz_generator")


def discover_candidates(state: AgentState) -> list[dict[str, Any]]:
    """Build chart configs from every successful DAG step."""
    raw_data = state.get("raw_data") or {}
    plan = state.get("execution_plan") or []
    seen_ids: set[str] = set()
    candidates: list[dict[str, Any]] = []

    if isinstance(raw_data, dict):
        for step in plan:
            step_id = step.get("step_id")
            tool_id = step.get("tool_id", "")
            if not step_id:
                continue
            data = raw_data.get(step_id)
            if data is None and tool_id == state.get("route_called") and len(plan) == 1:
                data = raw_data
            for chart in build_from_step(str(step_id), tool_id, data or {}):
                if chart["id"] not in seen_ids:
                    seen_ids.add(chart["id"])
                    candidates.append(chart)

        if not candidates and state.get("route_called"):
            route = state.get("route_called", "")
            for key, val in raw_data.items():
                if isinstance(val, dict):
                    for chart in build_from_step(str(key), route, val):
                        if chart["id"] not in seen_ids:
                            seen_ids.add(chart["id"])
                            candidates.append(chart)

    return candidates[:8]


def stream_visualizations(
    state: AgentState,
    llm_client: LLMClient,
) -> Iterator[dict[str, Any]]:
    """
    Yield SSE-ready event dicts:
      viz_planning, viz_plan, viz_ready, viz_error
    """
    candidates = discover_candidates(state)
    if not candidates:
        return

    yield {"type": "viz_planning", "content": "Designing visual insights…"}

    selected = plan_visualizations(
        query=state.get("user_query", ""),
        route_called=state.get("route_called", ""),
        intent=state.get("intent", ""),
        candidates=candidates,
        llm_client=llm_client,
    )
    if not selected:
        return

    yield {
        "type": "viz_plan",
        "visualizations": [
            {
                "id": c["id"],
                "title": c["title"],
                "subtitle": c.get("subtitle", ""),
                "chart_type": c["chart_type"],
                "status": "loading",
            }
            for c in selected
        ],
    }

    def _finalize(chart: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "viz_ready",
            "id": chart["id"],
            "chart": {
                "id": chart["id"],
                "title": chart["title"],
                "subtitle": chart.get("subtitle", ""),
                "chart_type": chart["chart_type"],
                "index_axis": chart.get("index_axis"),
                "data": chart["data"],
            },
        }

    with ThreadPoolExecutor(max_workers=min(4, len(selected))) as pool:
        futures = {pool.submit(_finalize, chart): chart["id"] for chart in selected}
        for future in as_completed(futures):
            viz_id = futures[future]
            try:
                yield future.result()
            except Exception as e:
                logger.error(f"Viz build failed for {viz_id}: {e}")
                yield {"type": "viz_error", "id": viz_id, "content": str(e)}


def serialize_viz_event(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"

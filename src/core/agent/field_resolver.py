"""
Resolve a field value from a prior tool step result.

Handles flat keys, NL2SQL row tables, and nested anomaly ranker lists.
"""

from typing import Any

_RANKED_LIST_KEYS = (
    "top_10_critical_products",
    "top_revenue_risk",
    "top_profit_risk",
    "most_unusual_products",
    "products_recovering",
    "products_improving",
)

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "target_date": ("target_date", "date"),
    "date": ("date", "target_date"),
}


def resolve_field(source_data: Any, field: str) -> Any:
    """Extract `field` from a tool result dict, including nested structures."""
    if not isinstance(source_data, dict) or source_data.get("error"):
        return None

    for candidate in _FIELD_ALIASES.get(field, (field,)):
        if candidate in source_data and source_data[candidate] is not None:
            return source_data[candidate]

        rows = source_data.get("rows")
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            val = rows[0].get(candidate)
            if val is not None:
                return val

        for key in _RANKED_LIST_KEYS:
            items = source_data.get(key)
            if isinstance(items, list) and items and isinstance(items[0], dict):
                val = items[0].get(candidate)
                if val is not None:
                    return val

        if candidate in ("date", "target_date"):
            daily = source_data.get("daily_details") or source_data.get("history") or []
            if isinstance(daily, list) and daily:
                last = daily[-1]
                if isinstance(last, dict):
                    val = last.get("date") or last.get("target_date")
                    if val is not None:
                        return str(val)[:10]

    return None


def resolve_from_prior_steps(
    step_results: dict[str, Any],
    plan: list[dict[str, Any]],
    current_step_id: str,
    field: str,
) -> Any:
    """Walk prior successful steps (newest first) to resolve a missing field."""
    prior_ids = [
        str(s.get("step_id"))
        for s in plan
        if str(s.get("step_id")) != current_step_id
    ]
    for step_id in reversed(prior_ids):
        result = step_results.get(step_id)
        if not isinstance(result, dict) or result.get("error"):
            continue
        val = resolve_field(result, field)
        if val is not None:
            return val
    return None

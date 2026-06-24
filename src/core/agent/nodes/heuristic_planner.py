"""
Heuristic DAG planner — fallback when the LLM planner or replanner fails.

Selects a pre-defined template from standard_dags based on structured query
signals, binds entities from the user query, then runs normalize_dag().
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any

from src.core.agent.templates.standard_dags import STANDARD_DAGS

_PRODUCT_ID = re.compile(r"\bP\d+\b", re.I)
_PLACEHOLDER_IDS = frozenset({"P001", "2025-01-05"})

_FORECAST = re.compile(r"\b(forecast|predict|projection|projected|future)\b", re.I)
_EXPLAIN = re.compile(r"\b(explain|why|driver|root cause|cause of|reason)\b", re.I)
_DECISION = re.compile(
    r"\b(recommend|recommendation|should we|should i|decision|strategy|"
    r"action plan|actionable|prioritized|hypotheses|diagnos)\b",
    re.I,
)
_SIMULATE = re.compile(r"\b(what if|what-if|simulate|simulation|scenario)\b", re.I)
_OPTIMIZE = re.compile(r"\b(optimi[sz]e|maximi[sz]e|minimi[sz]e|best discount|best price)\b", re.I)
_ANOMALY = re.compile(r"\b(anomal|outlier|unusual|spike|drop)\b", re.I)
_CHANNEL = re.compile(r"\b(channel|mobile app|amazon|website|nykaa)\b", re.I)
_TREND = re.compile(
    r"\b(trend|growth|slope|consecutive|underperform|declining|volatility|week over week)\b",
    re.I,
)
_COMPARE = re.compile(r"\b(compare|versus|\bvs\b|period over period|year over year)\b", re.I)
_SEASONALITY = re.compile(r"\b(seasonal|seasonality|day of week|weekend effect)\b", re.I)
_CAMPAIGN = re.compile(r"\b(campaign|roas|ctr|ad spend)\b", re.I)
_INVENTORY = re.compile(r"\b(inventory|stock|stockout|turnover)\b", re.I)
_REPOSITORY = re.compile(r"\b(past experiment|a/b test|historical report|past report)\b", re.I)
_SENSITIVITY = re.compile(r"\b(sensitiv|elasticit)\b", re.I)
_RANK_DISCOVERY = re.compile(
    r"\b(top|worst|best|largest|smallest|highest|lowest|rank|which product)\b",
    re.I,
)
_SIMPLE_LOOKUP = re.compile(
    r"\b(top\s+\d+|how many|count of|list (all )?(products?|items?)|"
    r"what (is|was) the total|sum of (revenue|profit|orders))\b",
    re.I,
)
_NOT_SIMPLE_LOOKUP = re.compile(
    r"\b(forecast|explain|why|recommend|simulate|optimi[sz]e|anomal|diagnos|"
    r"root cause|action plan|should we|decision|strategy)\b",
    re.I,
)
_METRIC = re.compile(
    r"\b(revenue|profit|orders|conversion(?:_rate)?|retention(?:_rate)?)\b",
    re.I,
)


@dataclass(frozen=True)
class QuerySignals:
    """Structured features extracted from the user query."""

    forecast: bool
    explain: bool
    decision: bool
    simulate: bool
    optimize: bool
    anomaly: bool
    channel: bool
    trend: bool
    compare: bool
    seasonality: bool
    campaign: bool
    inventory: bool
    repository: bool
    sensitivity: bool
    rank_discovery: bool
    simple_lookup: bool
    has_product_id: bool
    metric: str


def extract_query_signals(query: str, extracted_params: dict[str, Any] | None = None) -> QuerySignals:
    """Detect analytical needs implied by the query text."""
    from src.core.agent.nodes.dag_planner import extract_query_entities

    entities = extract_query_entities(query, extracted_params)
    has_product = bool(entities.get("product_id") or _PRODUCT_ID.search(query))

    metric_match = _METRIC.search(query)
    metric = "revenue"
    if metric_match:
        token = metric_match.group(1).lower()
        if "conversion" in token:
            metric = "conversion_rate"
        elif "retention" in token:
            metric = "retention_rate"
        else:
            metric = token

    simple = bool(_SIMPLE_LOOKUP.search(query)) and not _NOT_SIMPLE_LOOKUP.search(query)

    return QuerySignals(
        forecast=bool(_FORECAST.search(query)),
        explain=bool(_EXPLAIN.search(query)),
        decision=bool(_DECISION.search(query)),
        simulate=bool(_SIMULATE.search(query)),
        optimize=bool(_OPTIMIZE.search(query)),
        anomaly=bool(_ANOMALY.search(query)),
        channel=bool(_CHANNEL.search(query)),
        trend=bool(_TREND.search(query)),
        compare=bool(_COMPARE.search(query)),
        seasonality=bool(_SEASONALITY.search(query)),
        campaign=bool(_CAMPAIGN.search(query)),
        inventory=bool(_INVENTORY.search(query)),
        repository=bool(_REPOSITORY.search(query)),
        sensitivity=bool(_SENSITIVITY.search(query)),
        rank_discovery=bool(_RANK_DISCOVERY.search(query)),
        simple_lookup=simple,
        has_product_id=has_product,
        metric=metric,
    )


def _clone_steps(template_name: str) -> list[dict[str, Any]]:
    template = STANDARD_DAGS.get(template_name)
    if not template:
        raise KeyError(f"Unknown heuristic template: {template_name}")
    return copy.deepcopy(template)


def _bind_template_params(
    steps: list[dict[str, Any]],
    query: str,
    signals: QuerySignals,
    entities: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attach user query, entities, and metric defaults to template steps."""
    bound: list[dict[str, Any]] = []
    for step in steps:
        step_copy = dict(step)
        tool_id = step_copy.get("tool_id", "")
        params = dict(step_copy.get("params") or {})

        if tool_id in ("nl2sql_query", "decision_ask", "repository_search"):
            params["query"] = query

        if tool_id == "decision_ask" and entities.get("product_id"):
            params.setdefault("product_id", entities["product_id"])

        if tool_id in ("forecast_predict", "explain_prediction", "simulate_scenario", "optimize_parameters"):
            pid = entities.get("product_id")
            if pid and (not params.get("product_id") or params.get("product_id") in _PLACEHOLDER_IDS):
                params["product_id"] = pid

        if tool_id == "explain_prediction":
            params.setdefault("target_metric", signals.metric)
            if entities.get("date"):
                params.setdefault("date", entities["date"])

        if tool_id in ("analytics_trend", "anomaly_detect", "analysis_declining"):
            params.setdefault("metric", signals.metric)

        if tool_id == "anomaly_detect" and entities.get("date"):
            params.setdefault("target_date", entities["date"])
            params.setdefault("kpi", signals.metric)

        if tool_id == "anomaly_rank_products":
            if entities.get("date"):
                params.setdefault("date", entities["date"])
            params.setdefault("kpi", signals.metric)

        step_copy["params"] = params
        bound.append(step_copy)
    return bound


def select_heuristic_template(
    signals: QuerySignals,
    *,
    allow_nl2sql_only: bool = True,
) -> str | None:
    """
    Pick the best standard DAG template for the detected signals.

    Rules are ordered from most specific to least specific.
    """
    if signals.decision and (signals.channel or signals.trend):
        return "channel_trend_decision"

    if signals.forecast and signals.explain and signals.decision:
        return "forecast_explain_decision"

    if signals.forecast and signals.explain:
        return "forecast_explain_chain"

    if signals.forecast:
        return "forecast_request"

    if signals.anomaly and signals.explain and signals.decision:
        return "anomaly_explain_decision"

    if signals.anomaly and (signals.explain or signals.rank_discovery):
        return "anomaly_explain_chain"

    if signals.anomaly:
        return "anomaly_check"

    if signals.simulate and signals.decision:
        return "simulate_decision"

    if signals.simulate:
        return "scenario_simulation"

    if signals.optimize and signals.decision:
        return "optimize_decision"

    if signals.optimize:
        return "optimization_request"

    if signals.sensitivity:
        return "sensitivity_analysis"

    if signals.compare:
        return "period_comparison"

    if signals.repository:
        return "repository_search"

    if signals.seasonality:
        return "seasonality_analysis"

    if signals.campaign:
        return "campaign_analysis"

    if signals.inventory and signals.has_product_id:
        return "inventory_check"

    if signals.channel and signals.decision:
        return "channel_trend_decision"

    if signals.trend and signals.decision:
        return "channel_trend_decision"

    if signals.channel:
        return "channel_analysis"

    if signals.trend:
        return "trend_analysis"

    if signals.decision:
        return "decision_recommendation"

    if signals.simple_lookup and allow_nl2sql_only:
        return "data_lookup"

    if allow_nl2sql_only:
        return "data_lookup"

    if signals.decision or signals.explain or signals.forecast:
        return "channel_trend_decision"

    return None


def build_heuristic_dag(
    query: str,
    extracted_params: dict[str, Any] | None = None,
    *,
    allow_nl2sql_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Build a fallback execution plan without calling the LLM planner.

    Returns a normalized DAG ready for the executor.
    """
    from src.core.agent.nodes.dag_planner import extract_query_entities, normalize_dag

    signals = extract_query_signals(query, extracted_params)
    template_name = select_heuristic_template(signals, allow_nl2sql_only=allow_nl2sql_only)
    if template_name is None:
        return []

    entities = extract_query_entities(query, extracted_params)
    steps = _bind_template_params(_clone_steps(template_name), query, signals, entities)
    return normalize_dag(steps, query, extracted_params)


def is_substantive_heuristic_plan(dag: list[dict[str, Any]]) -> bool:
    """True when the heuristic plan is more than a lone NL2SQL lookup."""
    if not dag:
        return False
    if len(dag) > 1:
        return True
    return dag[0].get("tool_id") != "nl2sql_query"

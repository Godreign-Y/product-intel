"""
Capability Registry — defines every tool the planner can invoke.

Each entry documents the tool's purpose, exact input/output schemas,
source module, data dependency, and estimated latency so the LLM
planner can reason about which tools to chain and in what order.
"""

from typing import Any


CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {
    # ── Forecasting ──────────────────────────────────────────────────────
    "forecast_predict": {
        "description": "Predicts future KPI metrics (revenue, profit, orders, conversion_rate, retention_rate) using LightGBM autoregressive models.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "horizon_days": {"type": "int", "required": False, "default": 30},
        },
        "output_schema": "{ forecast_total_revenue: float, forecast_total_profit: float, forecast_total_orders: float, daily_details: [{date, revenue, profit, orders}] }",
        "output_fields": ["forecast_total_revenue", "forecast_total_profit", "forecast_total_orders", "daily_details"],
        "chains_into": ["explain_prediction", "simulate_scenario", "decision_ask"],
        "source_module": "src.core.forecaster.ProductForecaster.forecast",
        "requires_data": True,
        "estimated_latency": "medium",
    },

    # ── Explainability ───────────────────────────────────────────────────
    "explain_prediction": {
        "description": "Explains WHY a metric behaved a certain way on a specific date using SHAP values. Returns positive and negative drivers.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "target_metric": {"type": "str", "required": False, "default": "revenue", "options": ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]},
            "date": {"type": "str (YYYY-MM-DD)", "required": True},
        },
        "output_schema": "{ prediction_value: float, base_value: float, explanation_summary: str, positive_drivers: [{feature, clean_name, shap_value}], negative_drivers: [{feature, clean_name, shap_value}] }",
        "output_fields": ["prediction_value", "base_value", "explanation_summary", "positive_drivers", "negative_drivers"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.explainer.PredictionExplainer.explain_prediction",
        "requires_data": True,
        "estimated_latency": "medium",
    },
    "explain_global": {
        "description": "Returns the global feature importance ranking for a target metric.",
        "input_schema": {
            "target_metric": {"type": "str", "required": False, "default": "revenue"},
        },
        "output_schema": "[{ feature: str, clean_name: str, importance_value: float }]",
        "output_fields": ["feature", "clean_name", "importance_value"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.explainer.PredictionExplainer.get_global_importance",
        "requires_data": False,
        "estimated_latency": "fast",
    },

    # ── Scenario Simulation ──────────────────────────────────────────────
    "simulate_scenario": {
        "description": "Runs a what-if simulation by modifying business levers (discount, marketing, shipping, price) and measuring impact on all KPIs.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "horizon_days": {"type": "int", "required": False, "default": 30},
            "changes": {"type": "list[str]", "required": True, "examples": ["discount +5%", "marketing -10%", "shipping +20", "price =500"]},
        },
        "output_schema": "{ product_id: str, kpis: { revenue: {baseline, simulated, absolute_difference, percentage_difference, impact}, ... }, daily_comparison: {...} }",
        "output_fields": ["product_id", "kpis", "daily_comparison"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.simulator.ScenarioSimulator.evaluate_scenario",
        "requires_data": True,
        "estimated_latency": "slow",
    },

    # ── Optimization ─────────────────────────────────────────────────────
    "optimize_parameters": {
        "description": "Finds the optimal discount_pct and marketing_spend to maximize a target KPI via grid search.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "target_metric": {"type": "str", "required": False, "default": "revenue"},
            "horizon_days": {"type": "int", "required": False, "default": 30},
            "max_discount_pct": {"type": "float", "required": False, "default": 0.30},
            "max_marketing_budget": {"type": "float", "required": False, "default": 250.0},
        },
        "output_schema": "{ optimal_parameters: {discount_pct, marketing_spend, price}, baseline_forecast_sum: float, optimized_forecast_sum: float, percentage_improvement: float }",
        "output_fields": ["optimal_parameters", "baseline_forecast_sum", "optimized_forecast_sum", "percentage_improvement"],
        "chains_into": ["simulate_scenario", "decision_ask"],
        "source_module": "src.core.optimizer.RevenueOptimizer.optimize_parameters",
        "requires_data": True,
        "estimated_latency": "slow",
    },

    # ── Sensitivity ──────────────────────────────────────────────────────
    "sensitivity_estimate": {
        "description": "Estimates how sensitive revenue is to changes in marketing, discount, shipping, price, inventory, and retention.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "horizon_days": {"type": "int", "required": False, "default": 30},
        },
        "output_schema": "{ marketing: {elasticity_score, expected_impact, confidence}, discount: {...}, shipping: {...}, price: {...}, inventory: {...}, return: {...} }",
        "output_fields": ["marketing", "discount", "shipping", "price", "inventory", "return"],
        "chains_into": ["decision_ask", "optimize_parameters"],
        "source_module": "src.core.sensitivity.SensitivityEngine.calculate_sensitivity",
        "requires_data": True,
        "estimated_latency": "slow",
    },

    # ── Analytics Suite ──────────────────────────────────────────────────
    "analytics_kpi": {
        "description": "Returns KPI summary: total revenue, profit, orders, avg conversion/retention rates.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ total_revenue, total_profit, total_orders, avg_conversion_rate, avg_retention_rate, ... }",
        "output_fields": ["total_revenue", "total_profit", "total_orders", "avg_conversion_rate", "avg_retention_rate"],
        "chains_into": ["analysis_compare"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_kpis",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_trend": {
        "description": "Computes trend slope, growth rate, and daily values for a metric.",
        "input_schema": {
            "metric": {"type": "str", "required": False, "default": "revenue"},
            "product_id": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ slope, r_squared, growth_rate, daily_values[] }",
        "output_fields": ["slope", "r_squared", "growth_rate", "daily_values"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_trends",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_benchmark": {
        "description": "Benchmarks a product against its category average and global average.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ product_metrics, category_avg, global_avg, percentile_rank }",
        "output_fields": ["product_metrics", "category_avg", "global_avg", "percentile_rank"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_benchmarks",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_seasonality": {
        "description": "Analyzes day-of-week, weekend, and monthly seasonality patterns.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ day_of_week_pattern, monthly_pattern, weekend_effect }",
        "output_fields": ["day_of_week_pattern", "monthly_pattern", "weekend_effect"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_seasonality",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_channel": {
        "description": "Performance metrics across sales channels (Amazon, Website, Nykaa, Mobile App).",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ channel_breakdown[] }",
        "output_fields": ["channel_breakdown"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_channels",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_campaign": {
        "description": "Marketing campaign spend allocation and ROI analysis.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ campaign_summary, roi_metrics }",
        "output_fields": ["campaign_summary", "roi_metrics"],
        "chains_into": ["decision_ask", "optimize_parameters"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_campaigns",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_inventory": {
        "description": "Stock turnover rate, stock counts, and stockout risk analysis.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ stock_turnover, stockout_risk, avg_inventory }",
        "output_fields": ["stock_turnover", "stockout_risk", "avg_inventory"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_inventory",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_customer": {
        "description": "Customer metrics: LTV estimates, active user counts, age group distributions.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ ltv_estimate, active_users, age_groups }",
        "output_fields": ["ltv_estimate", "active_users", "age_groups"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_customers",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_marketing": {
        "description": "ROAS, CTR, and correlation between ad spend and revenue.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ roas, ctr, spend_revenue_correlation }",
        "output_fields": ["roas", "ctr", "spend_revenue_correlation"],
        "chains_into": ["decision_ask", "optimize_parameters"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_marketing",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analytics_pricing": {
        "description": "Performance by discount buckets and price elasticity estimate.",
        "input_schema": {
            "product_id": {"type": "str", "required": False},
            "category": {"type": "str", "required": False},
            "start_date": {"type": "str (YYYY-MM-DD)", "required": False},
            "end_date": {"type": "str (YYYY-MM-DD)", "required": False},
        },
        "output_schema": "{ discount_bucket_performance, price_elasticity }",
        "output_fields": ["discount_bucket_performance", "price_elasticity"],
        "chains_into": ["decision_ask", "optimize_parameters", "simulate_scenario"],
        "source_module": "src.core.analytics.engine.AnalyticsEngine.get_pricing",
        "requires_data": True,
        "estimated_latency": "fast",
    },

    # ── Anomaly Detection ────────────────────────────────────────────────
    "anomaly_detect": {
        "description": "Runs the full 15-layer anomaly detection pipeline for a product KPI on a target date.",
        "input_schema": {
            "product_id": {"type": "str", "required": True, "default": "P001"},
            "target_date": {"type": "str (YYYY-MM-DD)", "required": True},
            "kpi": {"type": "str", "required": False, "default": "revenue"},
        },
        "output_schema": "{ severity_score, status, explanation, business_impact, change_point_detected, ... }",
        "output_fields": ["severity_score", "status", "explanation", "business_impact", "change_point_detected"],
        "chains_into": ["explain_prediction", "decision_ask"],
        "source_module": "src.core.anomaly.engine.AnomalyDetectionEngine.run_detection",
        "requires_data": True,
        "estimated_latency": "slow",
    },
    "anomaly_rank_products": {
        "description": "Generates global anomaly ranking and risk profiles across all products for a date.",
        "input_schema": {
            "date": {"type": "str (YYYY-MM-DD)", "required": True},
            "kpi": {"type": "str", "required": False, "default": "revenue"},
        },
        "output_schema": "{ ranked_products[], risk_profiles }",
        "output_fields": ["ranked_products", "risk_profiles"],
        "chains_into": ["anomaly_detect", "explain_prediction"],
        "source_module": "src.core.anomaly.engine.AnomalyDetectionEngine.get_top_products",
        "requires_data": True,
        "estimated_latency": "slow",
    },

    # ── Business Analysis ────────────────────────────────────────────────
    "analysis_compare": {
        "description": "Compares business metrics between two custom date periods.",
        "input_schema": {
            "period1_start": {"type": "str (YYYY-MM-DD)", "required": True},
            "period1_end": {"type": "str (YYYY-MM-DD)", "required": True},
            "period2_start": {"type": "str (YYYY-MM-DD)", "required": True},
            "period2_end": {"type": "str (YYYY-MM-DD)", "required": True},
            "product_id": {"type": "str", "required": False},
        },
        "output_schema": "{ metrics_comparison: {revenue: {period1_sum, period2_sum, percentage_change}, ...}, drivers_summary[] }",
        "output_fields": ["metrics_comparison", "drivers_summary"],
        "chains_into": ["explain_prediction", "decision_ask"],
        "source_module": "src.core.analyzer.BusinessAnalyzer.compare_periods",
        "requires_data": True,
        "estimated_latency": "fast",
    },
    "analysis_declining": {
        "description": "Identifies products on a declining trend over a lookback window.",
        "input_schema": {
            "lookback_days": {"type": "int", "required": False, "default": 30},
            "metric": {"type": "str", "required": False, "default": "revenue"},
        },
        "output_schema": "{ declining_products: [{product_id, slope, percentage_change, r_squared}] }",
        "output_fields": ["declining_products"],
        "chains_into": ["explain_prediction", "anomaly_detect", "decision_ask"],
        "source_module": "src.core.analyzer.BusinessAnalyzer.detect_declining_products",
        "requires_data": True,
        "estimated_latency": "fast",
    },

    # ── Decision Intelligence ────────────────────────────────────────────
    "decision_ask": {
        "description": "Runs the full AI Scientist decision loop: context assembly, hypothesis generation, ML validation, confidence scoring, and recommendation.",
        "input_schema": {
            "query": {"type": "str", "required": True},
            "product_id": {"type": "str", "required": False, "default": "P001"},
            "session_id": {"type": "str", "required": False},
        },
        "output_schema": "{ ranked_hypotheses[], recommendations[], explanation: str }",
        "output_fields": ["ranked_hypotheses", "recommendations", "explanation"],
        "chains_into": [],
        "source_module": "src.core.decision.manager.DecisionManager.process_decision_flow",
        "requires_data": True,
        "estimated_latency": "slow",
    },

    # ── NL2SQL Data Lookup ───────────────────────────────────────────────
    "nl2sql_query": {
        "description": "Answers factual data questions by generating and running a validated read-only SQL query against product_performance, events, experiments, snapshots, reports, and knowledge_base.",
        "input_schema": {
            "query": {"type": "str", "required": True},
        },
        "output_schema": "{ query: str, sql: str, columns: [str], rows: [dict], row_count: int, truncated: bool }",
        "output_fields": ["query", "sql", "columns", "rows", "row_count", "truncated"],
        "chains_into": ["explain_prediction", "analytics_trend", "anomaly_detect", "analysis_compare", "forecast_predict"],
        "source_module": "src.core.nl2sql.engine.NL2SQLEngine.ask",
        "requires_data": False,
        "estimated_latency": "fast",
    },

    # ── History Repository ───────────────────────────────────────────────
    "repository_search": {
        "description": "Semantic search over historical reports, A/B tests, and experiments.",
        "input_schema": {
            "query": {"type": "str", "required": True},
        },
        "output_schema": "{ results_found: int, items: [{score, experiment_id, type, change_summary, outcome, structured_report}] }",
        "output_fields": ["results_found", "items"],
        "chains_into": ["decision_ask"],
        "source_module": "src.core.history.manager.HistoryManager.semantic_search",
        "requires_data": False,
        "estimated_latency": "fast",
    },
    "repository_extract": {
        "description": "Extracts topic-based insights and successful strategies from previous experiments.",
        "input_schema": {
            "query": {"type": "str", "required": False},
            "category": {"type": "str", "required": False, "options": ["pricing", "checkout", "discount", "shipping", "marketing"]},
        },
        "output_schema": "{ insights, successful_strategies, learnings }",
        "output_fields": ["insights", "successful_strategies", "learnings"],
        "chains_into": ["decision_ask", "simulate_scenario"],
        "source_module": "src.core.history.manager.HistoryManager.extract_topic_insights",
        "requires_data": False,
        "estimated_latency": "fast",
    },
}


def get_tool_descriptions_for_prompt() -> str:
    """Format the registry into a text block suitable for injection into LLM prompts."""
    lines: list[str] = []
    for tool_id, spec in CAPABILITY_REGISTRY.items():
        params = ", ".join(
            f"{k}: {v['type']}" + (f" (default={v['default']})" if "default" in v else "")
            for k, v in spec["input_schema"].items()
        )
        fields = ", ".join(spec.get("output_fields", []))
        chains = ", ".join(spec.get("chains_into", []))
        desc = f"- {tool_id}({params}): {spec['description']}"
        desc += f"\n  Output Fields: [{fields}]"
        if chains:
            desc += f"\n  Chains Into: [{chains}]"
        lines.append(desc)
    return "\n".join(lines)

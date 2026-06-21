import os
import json
import re
import pandas as pd
from typing import Dict, Any, Optional

from src.core.forecaster import ProductForecaster
from src.core.explainer import PredictionExplainer
from src.core.simulator import ScenarioSimulator
from src.core.optimizer import RevenueOptimizer
from src.core.analyzer import BusinessAnalyzer
from src.core.analytics.engine import AnalyticsEngine
from src.core.sensitivity import SensitivityEngine
from src.utils.logger import setup_logger

logger = setup_logger("planner_agent")


def _stream_text_and_visualizations(result: dict[str, Any], llm_client: Any):
    """Stream text synthesis and visualization events in parallel."""
    import queue
    import threading
    import time

    from src.core.agent.nodes.synthesizer import synthesize_response_stream
    from src.core.agent.visualization.generator import serialize_viz_event, stream_visualizations

    viz_queue: queue.Queue = queue.Queue()
    viz_done = threading.Event()

    def _run_viz() -> None:
        try:
            for event in stream_visualizations(result, llm_client):
                viz_queue.put(event)
        finally:
            viz_done.set()

    threading.Thread(target=_run_viz, daemon=True).start()

    def _drain_viz() -> list[str]:
        drained: list[str] = []
        while True:
            try:
                drained.append(serialize_viz_event(viz_queue.get_nowait()))
            except queue.Empty:
                break
        return drained

    for chunk in synthesize_response_stream(result, llm_client):
        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        for payload in _drain_viz():
            yield payload

    while not viz_done.is_set() or not viz_queue.empty():
        for payload in _drain_viz():
            yield payload
        if viz_done.is_set() and viz_queue.empty():
            break
        time.sleep(0.05)


class LLMPlannerAgent:
    def __init__(
        self,
        forecaster: ProductForecaster,
        explainer: PredictionExplainer,
        simulator: ScenarioSimulator,
        optimizer: RevenueOptimizer,
        analyzer: BusinessAnalyzer,
        analytics_engine: AnalyticsEngine,
        sensitivity_engine: SensitivityEngine,
        df_historical: Optional[pd.DataFrame] = None
    ):
        self.forecaster = forecaster
        self.explainer = explainer
        self.simulator = simulator
        self.optimizer = optimizer
        self.analyzer = analyzer
        self.analytics_engine = analytics_engine
        self.sensitivity_engine = sensitivity_engine
        self.df_historical = df_historical

        from src.core.llm import get_llm_client
        self.llm_client = get_llm_client()

    def route_and_extract(self, query: str) -> Dict[str, Any]:
        """
        Calls Llama 3.1 to select the correct API route and arguments based on user prompt.
        """
        if not self.llm_client:
            logger.warning("LLM client unavailable. Falling back to deterministic rule-based router.")
            return self._fallback_rule_based_router(query)
            
        system_prompt = (
            "You are a routing and extraction agent for a Business Intelligence microservice.\n"
            "Analyze the user's query and output a JSON object indicating the most relevant API action to perform.\n\n"
            "CRITICAL PRIORITY RULE:\n"
            "- If the query asks for a strategic recommendation, a business decision, a what-if planning scenario (e.g., queries starting with 'Should we...', 'What happens if...', 'What will happen to... if...'), a diagnostic of a drop/change, or any actionable recommendation advice, you MUST route it to 'decision_ask'. Do NOT route to 'sensitivity_estimate' or 'scenario_evaluate' if the user is asking a decision question like 'Should we...'.\n\n"
            "AVAILABLE ACTIONS & RULES:\n"
            "1. 'forecast_predict': For queries asking about predicting/forecasting future metrics (e.g. revenue, profit, conversion, orders).\n"
            "   Params: 'product_id' (str, default: 'P001'), 'horizon_days' (int, default: 30), 'target_metric' (str, e.g. 'revenue', 'profit', 'orders').\n"
            "2. 'explanation_explain': For queries asking WHY a prediction was made, or explaining a forecast driver on a specific date.\n"
            "   Params: 'product_id' (str, default: 'P001'), 'target_metric' (str, default: 'revenue'), 'date' (str, format YYYY-MM-DD, e.g. '2025-01-05').\n"
            "3. 'scenario_evaluate': For queries asking 'what-if' or scenario changes (e.g., 'if I decrease discount by 5 and increase shipping...').\n"
            "   Params: 'product_id' (str, default: 'P001'), 'horizon_days' (int, default: 30), 'changes' (list of str, e.g. ['discount -5%', 'shipping +20']).\n"
            "4. 'optimization_maximize': For queries asking how to maximize, optimize, or find best parameter configurations.\n"
            "   Params: 'target_metric' (str, default: 'revenue'), 'product_id' (str, default: 'P001'), 'horizon_days' (int, default: 30), 'max_discount_pct' (float, default: 0.30), 'max_marketing_budget' (float, default: 250.0).\n"
            "5. 'analysis_compare': For queries comparing metrics between two date periods.\n"
            "   Params: 'product_id' (str or null), 'period1_start' (str, YYYY-MM-DD), 'period1_end' (str, YYYY-MM-DD), 'period2_start' (str, YYYY-MM-DD), 'period2_end' (str, YYYY-MM-DD).\n"
            "6. 'analysis_declining': For queries asking to identify declining products or trends over a period.\n"
            "   Params: 'lookback_days' (int, default: 30), 'metric' (str, default: 'revenue').\n"
            "7. 'analytics_kpi': General performance summaries or totals of KPIs.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "8. 'analytics_trend': Historical trend calculations, growth rates, or slope fits.\n"
            "   Params: 'metric' (str, default: 'revenue'), 'product_id' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "9. 'analytics_benchmark': Benchmarking a product against peers/category.\n"
            "   Params: 'product_id' (str, default: 'P001'), 'start_date' (str or null), 'end_date' (str or null).\n"
            "10. 'analytics_seasonality': Analyzing day-of-week, weekend, or monthly seasonality distributions.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "11. 'analytics_channel': Performance metrics across sales channels (Amazon, Website, Nykaa, Mobile App).\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "12. 'analytics_campaign': Marketing campaign spend allocation/ROI.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "13. 'analytics_inventory': Stock turnover rate, stock counts, and stockout risks.\n"
            "   Params: 'product_id' (str, default: 'P001'), 'start_date' (str or null), 'end_date' (str or null).\n"
            "14. 'analytics_customer': Customer metrics like LTV, active users, age groups.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "15. 'analytics_marketing': ROAS, CTR, or correlation between ad spend and revenue.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "16. 'analytics_pricing': Performance by discount buckets and price elasticity estimate.\n"
            "   Params: 'product_id' (str or null), 'category' (str or null), 'start_date' (str or null), 'end_date' (str or null).\n"
            "17. 'sensitivity_estimate': Sensitivity of revenue to marketing, discount, shipping, price, inventory, return/retention.\n"
            "   Params: 'product_id' (str, default: 'P001'), 'horizon_days' (int, default: 30).\n"
            "18. 'repository_search': Semantic search for historical reports, A/B tests, funnel or pricing experiments.\n"
            "   Params: 'query' (str, the search query keywords/text).\n"
            "19. 'repository_extract': Extract topic-based insights, successful strategies and learnings from previous experiments.\n"
            "   Params: 'query' (str, e.g. 'checkout'), 'category' (str, topic name, e.g. 'checkout', 'pricing', 'discount').\n"
            "20. 'decision_ask': For strategic decisions, what-if questions, planning recommendations, diagnostics, or explaining performance drops.\n"
            "   Params: 'query' (str, the raw user query), 'product_id' (str, default: 'P001'), 'session_id' (str or null).\n\n"
            "OUTPUT FORMAT:\n"
            "You MUST reply with ONLY a JSON code block or raw JSON object containing two fields:\n"
            "{\n"
            "  \"route\": \"<chosen_action_name>\",\n"
            "  \"params\": { <extracted_parameters> }\n"
            "}\n"
            "Do not output markdown code blocks unless it is specifically formatted as raw JSON. Do not write text before or after the JSON."
        )
        
        try:
            result = self.llm_client.generate_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=300,
                model_tier="capable",
            )
            logger.info(f"LLM Routing Output: {result}")
            return result
        except Exception as e:
            logger.error(f"LLM routing failed: {e}. Falling back to rule-based.")
            return self._fallback_rule_based_router(query)

    def execute_route(self, route: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches routed actions to the underlying modules and returns the result.
        """
        logger.info(f"Executing route: {route} with params: {params}")
        
        df_hist = self.df_historical
        if df_hist is None:
            from src.api.dependencies import get_historical_df_from_db, get_max_date_from_db
            
            prod_id = params.get("product_id")
            cat = params.get("category")
            start = params.get("start_date") or params.get("period1_start")
            end = params.get("end_date") or params.get("period2_end")
            
            if route == "analysis_compare":
                df_hist = get_historical_df_from_db(
                    start_date=min(params.get("period1_start", "2025-01-01"), params.get("period2_start", "2025-01-01")),
                    end_date=max(params.get("period1_end", "2025-12-31"), params.get("period2_end", "2025-12-31")),
                    product_id=prod_id
                )
            elif route == "analysis_declining":
                max_date = get_max_date_from_db()
                lookback = params.get("lookback_days", 30)
                cutoff_date = max_date - pd.Timedelta(days=lookback)
                df_hist = get_historical_df_from_db(start_date=cutoff_date)
            elif route == "analytics_benchmark":
                df_hist = get_historical_df_from_db(
                    start_date=start,
                    end_date=end
                )
            else:
                df_hist = get_historical_df_from_db(
                    start_date=start,
                    end_date=end,
                    product_id=prod_id,
                    category=cat
                )
                
        original_df = self.df_historical
        self.df_historical = df_hist
        try:
            # 1. Forecast
            if route == "forecast_predict":
                horizon = params.get("horizon_days", 30)
                prod_id = params.get("product_id", "P001")
                # Run predictive all-target forecast to get full data context
                forecast_df = self.forecaster.forecast(
                    historical_df=self.df_historical,
                    product_id=prod_id,
                    horizon_days=horizon
                )
                
                # Format to a serializable dictionary
                forecast_records = []
                for _, row in forecast_df.iterrows():
                    forecast_records.append({
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "revenue": round(float(row["revenue"]), 2),
                        "profit": round(float(row["profit"]), 2),
                        "orders": round(float(row["orders"]), 2)
                    })
                return {
                    "product_id": prod_id,
                    "horizon_days": horizon,
                    "forecast_total_revenue": round(sum(r["revenue"] for r in forecast_records), 2),
                    "forecast_total_profit": round(sum(r["profit"] for r in forecast_records), 2),
                    "forecast_total_orders": round(sum(r["orders"] for r in forecast_records), 2),
                    "daily_details": forecast_records[:10]  # Cap to prevent token overflow
                }
                
            # 2. Explanations
            elif route == "explanation_explain":
                prod_id = params.get("product_id", "P001")
                metric = params.get("target_metric", "revenue")
                date = params.get("date", "2025-01-05")
                return self.explainer.explain_prediction(
                    historical_df=self.df_historical,
                    product_id=prod_id,
                    target_metric=metric,
                    date=date
                )
            elif route == "explanation_global":
                metric = params.get("target_metric", "revenue")
                return {
                    "target_metric": metric,
                    "global_importance": self.explainer.get_global_importance(metric)
                }
                
            # 3. Scenario evaluates
            elif route == "scenario_evaluate":
                prod_id = params.get("product_id", "P001")
                horizon = params.get("horizon_days", 30)
                changes = params.get("changes", [])
                if not changes:
                    # Parse from query if empty
                    changes = ["discount +5%", "marketing +10%"]
                return self.simulator.evaluate_scenario(
                    historical_df=self.df_historical,
                    product_id=prod_id,
                    horizon_days=horizon,
                    changes=changes
                )
                
            # 4. Optimizations
            elif route == "optimization_maximize":
                prod_id = params.get("product_id", "P001")
                metric = params.get("target_metric", "revenue")
                horizon = params.get("horizon_days", 30)
                
                max_discount = params.get("max_discount_pct")
                max_marketing = params.get("max_marketing_budget")
                
                kwargs = {}
                if max_discount is not None:
                    kwargs["max_discount_pct"] = float(max_discount)
                if max_marketing is not None:
                    kwargs["max_marketing_budget"] = float(max_marketing)
                    
                return self.optimizer.optimize_parameters(
                    historical_df=self.df_historical,
                    product_id=prod_id,
                    horizon_days=horizon,
                    target_metric=metric,
                    **kwargs
                )
                
            # 5. Analysis
            elif route == "analysis_compare":
                p1_start = params.get("period1_start", "2025-01-01")
                p1_end = params.get("period1_end", "2025-01-15")
                p2_start = params.get("period2_start", "2025-01-16")
                p2_end = params.get("period2_end", "2025-01-30")
                prod_id = params.get("product_id")
                return self.analyzer.compare_periods(
                    df=self.df_historical,
                    period1_start=p1_start,
                    period1_end=p1_end,
                    period2_start=p2_start,
                    period2_end=p2_end,
                    product_id=prod_id
                )
            elif route == "analysis_declining":
                lookback = params.get("lookback_days", 30)
                metric = params.get("metric", "revenue")
                return {
                    "metric": metric,
                    "lookback_days": lookback,
                    "declining_products": self.analyzer.detect_declining_products(
                        df=self.df_historical,
                        lookback_days=lookback,
                        metric=metric
                    )[:10]
                }
                
            # 6. Analytics modules
            elif route == "analytics_kpi":
                return self.analytics_engine.get_kpis(
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date"),
                    product_id=params.get("product_id"),
                    category=params.get("category")
                )
            elif route == "analytics_trend":
                return self.analytics_engine.get_trends(
                    metric=params.get("metric", "revenue"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date"),
                    product_id=params.get("product_id")
                )
            elif route == "analytics_benchmark":
                return self.analytics_engine.get_benchmarks(
                    product_id=params.get("product_id", "P001"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_seasonality":
                return self.analytics_engine.get_seasonality(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_channel":
                return self.analytics_engine.get_channels(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_campaign":
                return self.analytics_engine.get_campaigns(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_inventory":
                return self.analytics_engine.get_inventory(
                    product_id=params.get("product_id", "P001"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_customer":
                return self.analytics_engine.get_customers(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_marketing":
                return self.analytics_engine.get_marketing(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
            elif route == "analytics_pricing":
                return self.analytics_engine.get_pricing(
                    product_id=params.get("product_id"),
                    category=params.get("category"),
                    start_date=params.get("start_date"),
                    end_date=params.get("end_date")
                )
                
            # 7. Sensitivity
            elif route == "sensitivity_estimate":
                prod_id = params.get("product_id", "P001")
                horizon = params.get("horizon_days", 30)
                return self.sensitivity_engine.calculate_sensitivity(
                    historical_df=self.df_historical,
                    product_id=prod_id,
                    horizon_days=horizon
                )
            elif route == "repository_search":
                query_str = params.get("query") or "pricing experiments"
                from src.core.history.storage.database import SessionLocal
                from src.core.history.manager import HistoryManager
                db = SessionLocal()
                try:
                    from src.api.dependencies import AppState
                    encoder = getattr(AppState, "history_encoder", None)
                    mgr = HistoryManager(db, encoder=encoder)
                    results = mgr.semantic_search(query_str, limit=5)
                    ser_results = []
                    for res in results:
                        ser_results.append({
                            "score": res["score"],
                            "experiment_id": res["experiment"].experiment_id,
                            "type": res["experiment"].type,
                            "change_summary": res["experiment"].change_summary,
                            "outcome": res["experiment"].outcome,
                            "structured_report": res["report"].structured_json
                        })
                    return {
                        "query": query_str,
                        "results_found": len(ser_results),
                        "items": ser_results
                    }
                finally:
                    db.close()
            elif route == "repository_extract":
                topic = params.get("category") or params.get("query") or "pricing"
                from src.core.history.storage.database import SessionLocal
                from src.core.history.manager import HistoryManager
                db = SessionLocal()
                try:
                    from src.api.dependencies import AppState
                    encoder = getattr(AppState, "history_encoder", None)
                    mgr = HistoryManager(db, encoder=encoder)
                    insights = mgr.extract_topic_insights(topic)
                    return insights
                finally:
                    db.close()
            elif route == "decision_ask":
                # Call DecisionManager dynamically
                from src.core.history.storage.database import SessionLocal
                from src.core.decision.manager import DecisionManager
                from src.core.history.manager import HistoryManager
                from src.api.dependencies import AppState
                
                db = SessionLocal()
                try:
                    history_encoder = getattr(AppState, "history_encoder", None)
                    history_mgr = HistoryManager(db, encoder=history_encoder)
                    
                    manager = DecisionManager(
                        db=db,
                        df_historical=self.df_historical,
                        forecaster=self.forecaster,
                        sensitivity_engine=self.sensitivity_engine,
                        simulator=self.simulator,
                        history_manager=history_mgr
                    )
                    
                    query_str = params.get("query") or params.get("q")
                    # Run the full decision flow
                    result = manager.process_decision_flow(
                        query=query_str,
                        product_id=params.get("product_id", "P001"),
                        session_id=params.get("session_id")
                    )
                    return result
                finally:
                    db.close()
            else:
                raise ValueError(f"Unknown routed action: {route}")
        except Exception as e:
            logger.error(f"Execution failed for route {route}: {e}")
            return {"error": f"Failed to execute calculation: {str(e)}"}
        finally:
            self.df_historical = original_df

    def synthesize_answer(self, query: str, route: str, raw_data: Dict[str, Any]) -> str:
        """
        Asks Llama 3.1 to generate a polished natural language report translating the JSON output into insights.
        """
        if route == "decision_ask" and "explanation" in raw_data:
            return raw_data["explanation"]

        if not self.llm_client:
            return (
                f"Deterministically executed route '{route}'. Here is the computed data:\n"
                f"{json.dumps(raw_data, indent=2)}\n"
                "Please configure an LLM provider to receive synthesized natural language summaries."
            )
            
        system_prompt = (
            "You are a helpful and professional Business Intelligence Assistant chatbot.\n"
            "The user asked a question. You resolved the request by running an analytics model, which returned raw JSON data.\n"
            "Summarize the analytical results and explain the answer clearly in natural language.\n"
            "Format the response using professional markdown with bullet points or tables where appropriate.\n"
            "Highlight the most critical business recommendations or insights derived from the numbers.\n"
            "Do not reference technical details like 'route chosen', 'raw JSON', or internal database variables unless necessary. Speak directly to the business user."
        )
        
        user_content = (
            f"User Query: \"{query}\"\n"
            f"Executed Action: \"{route}\"\n"
            f"Raw Data Result:\n{json.dumps(raw_data, indent=2)}"
        )
        
        try:
            return self.llm_client.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=600,
                model_tier="fast",
            )
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return (
                f"Calculations completed successfully. Here is the raw computed result:\n\n"
                f"{json.dumps(raw_data, indent=2)}\n\n"
                f"(Note: Conversation synthesis failed due to: {str(e)})"
            )

    def process_query_stream(self, query: str):
        """
        Performs the complete agent workflow via LangGraph pipeline, yielding Server-Sent Events.
        """
        # ── Try LangGraph pipeline first ─────────────────────────────
        try:
            from src.core.agent.graph import run_agent_graph, _compiled_graph, _llm_client
            from src.core.agent.nodes.synthesizer import synthesize_response_stream
            
            if _compiled_graph is not None:
                # Construct the initial graph state
                from src.core.agent.state import AgentState
                initial_state: AgentState = {
                    "user_query": query,
                    "intent": "",
                    "intent_confidence": 0.0,
                    "extracted_params": {},
                    "is_blocked": False,
                    "block_reason": "",
                    "dag_source": "",
                    "execution_plan": [],
                    "current_step_index": 0,
                    "step_results": {},
                    "execution_errors": [],
                    "validation_passed": True,
                    "validation_notes": "",
                    "retry_count": 0,
                    "final_response": "",
                    "raw_data": {},
                    "route_called": "",
                }
                
                result = initial_state
                yield f"data: {json.dumps({'type': 'status', 'content': 'Classifying query intent...'})}\n\n"
                
                # Stream node by node
                for event in _compiled_graph.stream(initial_state):
                    for node_name, state_update in event.items():
                        # Update our local accumulated state
                        result = {**result, **state_update}
                        
                        # Yield status updates for each node type
                        if node_name == "intent_classifier":
                            intent = result.get("intent", "analytical")
                            conf = result.get("intent_confidence", 1.0)
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Classified intent: {intent} ({conf*100:.0f}% confidence)'})}\n\n"
                        elif node_name == "dag_planner":
                            plan = result.get("execution_plan", [])
                            tool_ids = [
                                s.get("tool_id", s.get("step_id", "?"))
                                for s in plan
                                if isinstance(s, dict)
                            ]
                            plan_str = f" ({', '.join(tool_ids)})" if tool_ids else ""
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Formulating analytics plan{plan_str}...'})}\n\n"
                        elif node_name == "dag_executor":
                            steps = result.get("execution_plan", [])
                            idx = result.get("current_step_index", 0)
                            step = steps[idx] if steps and idx < len(steps) else {}
                            step_label = step.get("tool_id", step.get("step_id", "")) if isinstance(step, dict) else str(step)
                            step_info = f" (Step {idx + 1}/{len(steps)}: {step_label})" if step_label else ""
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Running mathematical calculations{step_info}...'})}\n\n"
                        elif node_name == "validator":
                            passed = result.get("validation_passed", True)
                            status_text = "passed" if passed else "flagged inconsistencies"
                            yield f"data: {json.dumps({'type': 'status', 'content': f'Validating model output... validation {status_text}.'})}\n\n"
                        elif node_name == "replanner":
                            yield f"data: {json.dumps({'type': 'status', 'content': 'Adjusting parameters for refinement...'})}\n\n"
                        elif node_name == "fast_response":
                            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating fast summary...'})}\n\n"

                meta_chunk = {
                    "type": "metadata",
                    "query": result.get("user_query", query),
                    "route_called": result.get("route_called", ""),
                    "raw_data": result.get("raw_data", {})
                }
                yield f"data: {json.dumps(meta_chunk)}\n\n"

                yield from _stream_text_and_visualizations(result, _llm_client)
                yield "data: [DONE]\n\n"
                return
                
        except Exception as e:
            logger.warning(f"LangGraph pipeline failed, falling back to legacy: {e}")

        # ── Legacy fallback ──────────────────────────────────────────
        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing query intent (legacy)...'})}\n\n"
        routing_info = self.route_and_extract(query)
        route = routing_info.get("route", "forecast_predict")
        params = routing_info.get("params", {})
        if "query" not in params:
            params["query"] = query

        yield f"data: {json.dumps({'type': 'status', 'content': f'Running legacy calculation: {route}...'})}\n\n"
        raw_data = self.execute_route(route, params)
        
        meta_chunk = {
            "type": "metadata",
            "query": query,
            "route_called": route,
            "raw_data": raw_data
        }
        yield f"data: {json.dumps(meta_chunk)}\n\n"

        legacy_state = {
            "user_query": query,
            "intent": "analytical",
            "route_called": route,
            "raw_data": {"s1": raw_data},
            "execution_plan": [{"step_id": "s1", "tool_id": route, "params": params, "depends_on": []}],
        }
        yield from _stream_text_and_visualizations(legacy_state, self.llm_client)
        yield "data: [DONE]\n\n"

    def _fallback_rule_based_router(self, query: str) -> Dict[str, Any]:
        """
        Simple deterministic router fallback for local test stability.
        """
        q = query.lower()
        
        # 0. Decision Intelligence / AI Scientist Strategic Queries
        if any(k in q for k in ["should we", "what if", "what-if", "what will happen", "explain the recent", "performance drop", "decline"]):
            return {"route": "decision_ask", "params": {"query": query, "product_id": "P001"}}
            
        # 1. Sensitivity
        if "sensitivity" in q or "sensitive" in q or "elasticity" in q:
            return {"route": "sensitivity_estimate", "params": {"product_id": "P001", "horizon_days": 30}}
            
        # 2. Scenario evaluates
        elif "what-if" in q or "what if" in q or "scenario" in q or "if i decrease" in q or "if i increase" in q:
            changes = []
            if "discount" in q:
                changes.append("discount -5%")
            if "shipping" in q:
                changes.append("shipping +20")
            if "marketing" in q:
                changes.append("marketing +10%")
            return {"route": "scenario_evaluate", "params": {"product_id": "P001", "changes": changes, "horizon_days": 30}}
            
        # 3. Optimization
        elif "maximize" in q or "optimize" in q or "best" in q:
            target = "revenue"
            if "profit" in q:
                target = "profit"
            params = {"target_metric": target, "product_id": "P001", "horizon_days": 30}
            
            # Extract product id if P\d+ is in query
            prod_match = re.search(r"p\d+", q)
            if prod_match:
                params["product_id"] = prod_match.group(0).upper()
                
            # Extract budget if present
            budget_match = re.search(r"budget\s*(?:of|is|limit|cap)?\s*\$?\s*(\d+)", q)
            if budget_match:
                params["max_marketing_budget"] = float(budget_match.group(1))
                
            return {"route": "optimization_maximize", "params": params}
            
        # 4. Compare
        elif "compare" in q or "period-over-period" in q or "pop" in q:
            return {
                "route": "analysis_compare",
                "params": {
                    "product_id": "P001",
                    "period1_start": "2025-01-01",
                    "period1_end": "2025-01-15",
                    "period2_start": "2025-01-16",
                    "period2_end": "2025-01-30"
                }
            }
            
        # 5. Explanations / SHAP
        elif "why" in q or "explain" in q or "driver" in q:
            return {"route": "explanation_explain", "params": {"product_id": "P001", "target_metric": "revenue", "date": "2025-01-05"}}
            
        # 6. Benchmarks
        elif "benchmark" in q or "compare against peers" in q:
            return {"route": "analytics_benchmark", "params": {"product_id": "P001"}}
            
        # 7. Trends
        elif "trend" in q or "declining" in q:
            if "declining" in q:
                return {"route": "analysis_declining", "params": {"lookback_days": 30, "metric": "revenue"}}
            return {"route": "analytics_trend", "params": {"metric": "revenue", "product_id": "P001"}}
            
        # 8. History Repository / Experiments
        elif any(k in q for k in ["report", "experiment", "ab test", "learnings", "past", "historical", "tried", "conversion improvements"]):
            if any(k in q for k in ["learning", "summarize", "pattern", "insights", "strategy"]):
                # Extract topic category
                category = "pricing"
                if "checkout" in q or "conversion" in q:
                    category = "checkout"
                elif "discount" in q:
                    category = "discount"
                elif "shipping" in q:
                    category = "shipping"
                return {"route": "repository_extract", "params": {"query": q, "category": category}}
            else:
                return {"route": "repository_search", "params": {"query": query}}
                
        # 9. Forecast / Default
        else:
            return {"route": "forecast_predict", "params": {"product_id": "P001", "horizon_days": 30}}

import os
import json
import re
import pandas as pd
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from src.core.forecaster import ProductForecaster
from src.core.explainer import PredictionExplainer
from src.core.simulator import ScenarioSimulator
from src.core.optimizer import RevenueOptimizer
from src.core.analyzer import BusinessAnalyzer
from src.core.analytics.engine import AnalyticsEngine
from src.core.sensitivity import SensitivityEngine
from src.utils.logger import setup_logger

logger = setup_logger("planner_agent")

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
        df_historical: pd.DataFrame
    ):
        self.forecaster = forecaster
        self.explainer = explainer
        self.simulator = simulator
        self.optimizer = optimizer
        self.analyzer = analyzer
        self.analytics_engine = analytics_engine
        self.sensitivity_engine = sensitivity_engine
        self.df_historical = df_historical
        
        # Load API key and initialize client
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-70b-instruct"
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not found in environment variables. LLM client will fail if called.")
            self.client = None
        else:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=None)

    def route_and_extract(self, query: str) -> Dict[str, Any]:
        """
        Calls Llama 3.1 to select the correct API route and arguments based on user prompt.
        """
        if not self.client:
            # Fallback mock routing if API key is not present (mainly for testing environment)
            logger.warning("No LLM client initialized. Falling back to deterministic rule-based router.")
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=300
            )
            raw_text = response.choices[0].message.content.strip()
            logger.info(f"LLM Routing Output: {raw_text}")
            
            # Extract JSON from the text
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return json.loads(raw_text)
        except Exception as e:
            logger.error(f"LLM routing failed: {e}. Falling back to rule-based.")
            return self._fallback_rule_based_router(query)

    def execute_route(self, route: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches routed actions to the underlying modules and returns the result.
        """
        logger.info(f"Executing route: {route} with params: {params}")
        
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

    def synthesize_answer(self, query: str, route: str, raw_data: Dict[str, Any]) -> str:
        """
        Asks Llama 3.1 to generate a polished natural language report translating the JSON output into insights.
        """
        if route == "decision_ask" and "explanation" in raw_data:
            return raw_data["explanation"]

        if not self.client:
            return (
                f"Deterministically executed route '{route}'. Here is the computed data:\n"
                f"{json.dumps(raw_data, indent=2)}\n"
                "Please configure NVIDIA_API_KEY to receive synthesized natural language summaries."
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return (
                f"Calculations completed successfully. Here is the raw computed result:\n\n"
                f"{json.dumps(raw_data, indent=2)}\n\n"
                f"(Note: Conversation synthesis failed due to: {str(e)})"
            )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Performs the complete agent workflow: Select Route -> Execute calculation -> Synthesize answer.
        """
        routing_info = self.route_and_extract(query)
        route = routing_info.get("route", "forecast_predict")
        params = routing_info.get("params", {})
        
        # Ensure query is in params so executing components can access the raw text
        if "query" not in params:
            params["query"] = query
        
        raw_data = self.execute_route(route, params)
        natural_language_answer = self.synthesize_answer(query, route, raw_data)
        
        return {
            "query": query,
            "route_called": route,
            "raw_data": raw_data,
            "response": natural_language_answer
        }

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

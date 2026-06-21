import os
import json
import re
import datetime
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from src.utils.logger import setup_logger

logger = setup_logger("hypothesis_generator")

class HypothesisGenerator:
    def __init__(
        self, 
        db: Optional[Any] = None, 
        forecaster: Optional[Any] = None, 
        explainer: Optional[Any] = None, 
        history_manager: Optional[Any] = None
    ):
        self.db = db
        self.forecaster = forecaster
        self.explainer = explainer
        self.history_manager = history_manager

        # Initialize API client for Llama 3.1 instruct model via NVIDIA NIM
        load_dotenv()
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "meta/llama-3.1-70b-instruct"
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not found in environment variables. HypothesisGenerator will default to rule-based fallback candidates.")
            self.client = None
        else:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=None)

    def _determine_target_kpi(self, query: str) -> str:
        """
        Parses query to determine the primary target KPI of interest.
        """
        q = query.lower()
        if "profit" in q or "margin" in q:
            return "profit"
        elif "conversion" in q or "checkout" in q or "ctr" in q:
            return "conversion_rate"
        elif "order" in q or "sales volume" in q:
            return "orders"
        return "revenue" # Default KPI

    def _get_shap_features(self, target_kpi: str) -> List[Dict[str, Any]]:
        """
        Gets global feature importance list for the selected target KPI.
        """
        if not self.explainer:
            return []
        try:
            # Explainer maps KPIs using capitalized keys (e.g. Revenue, Profit, Conversion_Rate, Orders)
            kpi_map = {
                "revenue": "revenue",
                "profit": "profit",
                "orders": "orders",
                "conversion_rate": "conversion_rate"
            }
            mapped_kpi = kpi_map.get(target_kpi.lower(), "revenue")
            return self.explainer.get_global_importance(mapped_kpi)
        except Exception as e:
            logger.error(f"Failed to retrieve SHAP features for {target_kpi}: {e}")
            return []

    def _get_past_experiments(self, target_kpi: str) -> List[str]:
        """
        Retrieves matching similar experiments from database.
        """
        if not self.db:
            return []
        try:
            from src.core.history.storage.models import Experiment
            
            # Query the database for recent experiments
            db_exps = self.db.query(Experiment).order_by(Experiment.start_date.desc()).limit(10).all()
            
            matches = []
            for exp in db_exps:
                matches.append(
                    f"Experiment {exp.experiment_id} ({exp.type}): Tested {exp.change_summary} "
                    f"resulting in a {exp.outcome.upper()} outcome with statistical improvement of {exp.improvement_pct}%."
                )
            return matches
        except Exception as e:
            logger.error(f"Failed to retrieve past experiments: {e}")
            return []

    def _get_knowledge_base_rules(self) -> List[str]:
        """
        Retrieves business rules from the Knowledge Base table.
        """
        if not self.db:
            return []
        try:
            from src.core.history.storage.models import KnowledgeBase
            rules = self.db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).limit(10).all()
            
            rules_list = []
            for r in rules:
                rules_list.append(f"Pattern Type: {r.pattern_type} | Synthesized Rules: {json.dumps(r.synthesized_rules)}")
            return rules_list
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge base rules: {e}")
            return []

    def generate_candidates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Assembles data signals and uses the LLM to generate 10–20 hypotheses,
        then scores and ranks them, returning the top 3–5 candidate hypotheses.
        """
        query = context.get("query", "")
        product_id = context.get("product_id", "P001")
        
        # 1. Parse target KPI
        target_kpi = self._determine_target_kpi(query)
        
        # 2. Retrieve SHAP values & past experiments (aggregated if query is objective-agnostic)
        q_lower = query.lower()
        is_explicit = any(k in q_lower for k in ["revenue", "profit", "margin", "conversion", "checkout", "ctr", "order", "sales volume"])
        
        if not is_explicit:
            shap_importance = []
            seen_features = set()
            for kpi in ["revenue", "profit", "orders", "conversion_rate"]:
                kpi_shap = self._get_shap_features(kpi)
                for feat in kpi_shap:
                    feat_name = feat["clean_name"]
                    if feat_name not in seen_features:
                        seen_features.add(feat_name)
                        feat_with_tag = feat.copy()
                        feat_with_tag["clean_name"] = f"{feat_name} (drives {kpi.replace('_', ' ')})"
                        shap_importance.append(feat_with_tag)
                        
            # Sort by absolute SHAP impact value
            shap_importance.sort(key=lambda x: abs(x.get("importance_value", 0.0)), reverse=True)
            
            past_exps = []
            for kpi in ["revenue", "profit", "orders", "conversion_rate"]:
                past_exps.extend(self._get_past_experiments(kpi))
                
            seen_exps = set()
            unique_past_exps = []
            for e in past_exps:
                if e not in seen_exps:
                    seen_exps.add(e)
                    unique_past_exps.append(e)
            past_exps = unique_past_exps
        else:
            shap_importance = self._get_shap_features(target_kpi)
            past_exps = self._get_past_experiments(target_kpi)
            
        shap_summary = "\n".join([f"- {f['clean_name']} (SHAP Impact: {f['importance_value']})" for f in shap_importance[:8]])
        past_exps_summary = "\n".join([f"- {e}" for e in past_exps[:8]])
        
        # 4. Retrieve KB rules
        kb_rules = self._get_knowledge_base_rules()
        kb_rules_summary = "\n".join([f"- {r}" for r in kb_rules[:5]])

        # 5. Formulate candidates using LLM (if client available) or Fallback Templates
        candidates = []
        if self.client:
            candidates = self._generate_llm_candidates(
                query, target_kpi, shap_summary, past_exps_summary, kb_rules_summary, context
            )
            
        if not candidates:
            logger.info("Using template-based candidates fallback.")
            candidates = self._generate_fallback_candidates(query, target_kpi, context)

        # 6. Score and Rank candidates
        scored_candidates = []
        for cand in candidates:
            score_data = self._score_candidate(cand, shap_importance, past_exps, context)
            cand.update(score_data)
            scored_candidates.append(cand)

        # Sort descending by composite score
        scored_candidates = sorted(scored_candidates, key=lambda x: x["generator_score"], reverse=True)
        
        # Return top 3-5 candidates
        pruned_candidates = scored_candidates[:5]
        
        # Clean scores from output to match baseline DecisionManager schema
        for c in pruned_candidates:
            c.pop("generator_score", None)
            c.pop("score_breakdown", None)
            
        logger.info(f"Generated and pruned to {len(pruned_candidates)} candidate hypotheses.")
        return pruned_candidates

    def _generate_llm_candidates(
        self, 
        query: str, 
        target_kpi: str, 
        shap_summary: str, 
        past_exps_summary: str, 
        kb_rules_summary: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Asks Llama 3.1 to generate a list of 10 to 20 candidate business hypotheses in JSON format.
        """
        system_prompt = (
            "You are a professional Business Intelligence Analyst.\n"
            "Generate 10 to 20 candidate hypotheses matching the business context, query, and statistical drivers.\n\n"
            "CONSTRAINT RULES:\n"
            "1. Each hypothesis MUST map to ONE of the following real database driver variables:\n"
            "   - 'discount_pct'\n"
            "   - 'shipping_fee'\n"
            "   - 'avg_selling_price'\n"
            "   - 'marketing_spend'\n"
            "2. Each hypothesis MUST list one or more affected KPIs from: ['total_revenue', 'total_profit', 'total_orders', 'mean_conversion_rate'].\n"
            "3. The returned JSON structure MUST be a list of objects containing exactly these fields:\n"
            "   - 'hypothesis_id': Unique identifier (e.g. 'HYP_DIS_01', 'HYP_PRI_02')\n"
            "   - 'title': Clear business statement (e.g. 'Price increases decrease Customer Conversion')\n"
            "   - 'description': Multi-sentence description explaining the reasoning\n"
            "   - 'generated_from': Set to one of: 'SHAP Feature Importance', 'Historical Experiments', 'Knowledge Base Pattern', 'Correlation Heuristics'\n"
            "   - 'affected_kpis': List of string KPIs affected\n"
            "   - 'driver_variable': The mapped database driver column (must be exactly 'discount_pct', 'shipping_fee', 'avg_selling_price', or 'marketing_spend')\n"
            "   - 'confidence_prior': Prior confidence score between 0.0 and 1.0 (float)\n\n"
            "Respond with raw JSON only. Do not wrap in markdown or write text before/after."
        )

        user_prompt = (
            f"User query: \"{query}\"\n"
            f"Target KPI: {target_kpi}\n"
            f"Active Trends: {json.dumps(context.get('trends', {}))}\n"
            f"Active Anomalies: {json.dumps(context.get('anomalies', []))}\n\n"
            f"SHAP Global Feature Importance:\n{shap_summary or 'No active SHAP data.'}\n\n"
            f"Similar Past Experiments:\n{past_exps_summary or 'No similar past experiments found.'}\n\n"
            f"Business Knowledge Base Rules:\n{kb_rules_summary or 'No rules cached.'}\n"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            raw_text = response.choices[0].message.content.strip()
            
            # Extract JSON list
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(raw_text)
                
            if isinstance(data, list) and len(data) >= 5:
                return data
        except Exception as e:
            logger.error(f"LLM candidate hypothesis generation failed: {e}")
        return []

    def _generate_fallback_candidates(self, query: str, target_kpi: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Template-based fallback generating 10 structured candidates across variables.
        Enriches descriptions with actual KPI values from context when available.
        """
        q = query.lower()
        candidates = []

        # Extract KPI values for enriched descriptions
        kpis = (context or {}).get("kpis", {})
        revenue_str = f"${kpis.get('total_revenue', 0):,.0f}" if kpis.get('total_revenue') else "current levels"
        profit_str = f"${kpis.get('total_profit', 0):,.0f}" if kpis.get('total_profit') else "current levels"
        orders_str = f"{kpis.get('total_orders', 0):,}" if kpis.get('total_orders') else "current volume"
        conv_str = f"{kpis.get('mean_conversion_rate', 0):.2%}" if kpis.get('mean_conversion_rate') else "current rate"
        price_str = f"${kpis.get('avg_price', 0):,.2f}" if kpis.get('avg_price') else "current price"
        disc_str = f"{kpis.get('avg_discount_pct', 0):.1f}%" if kpis.get('avg_discount_pct') else "current discount"

        # 1. Price candidates
        candidates.append({
            "hypothesis_id": "HYP_PRI_01",
            "title": "Price increases decrease Customer Conversion",
            "description": f"Current avg selling price is {price_str} with conversion at {conv_str}. Increasing the average selling price creates consumer friction and decreases checkout conversion rates.",
            "generated_from": "Correlation Heuristics",
            "affected_kpis": ["mean_conversion_rate"],
            "driver_variable": "avg_selling_price",
            "confidence_prior": 0.75
        })
        candidates.append({
            "hypothesis_id": "HYP_PRI_02",
            "title": "Optimal selling price drives higher Revenue",
            "description": f"Current revenue is {revenue_str} at avg price {price_str}. Adjusting the selling price to match product elasticity bounds optimizes daily revenue return.",
            "generated_from": "Knowledge Base Pattern",
            "affected_kpis": ["total_revenue"],
            "driver_variable": "avg_selling_price",
            "confidence_prior": 0.65
        })

        # 2. Discount candidates
        candidates.append({
            "hypothesis_id": "HYP_DIS_01",
            "title": "Higher discounts increase Order Volume",
            "description": f"Current discount is {disc_str} with {orders_str} orders. Increasing the average discount percentage drives higher sales volumes but impacts profitability.",
            "generated_from": "Historical Experiments",
            "affected_kpis": ["total_orders", "total_revenue"],
            "driver_variable": "discount_pct",
            "confidence_prior": 0.70
        })
        candidates.append({
            "hypothesis_id": "HYP_DIS_02",
            "title": "Excessive discounts erode net Profitability",
            "description": f"Current profit is {profit_str} with discount at {disc_str}. Excessive discounting beyond product margin elasticity limits results in net profit deterioration.",
            "generated_from": "Sensitivity Analysis",
            "affected_kpis": ["total_profit"],
            "driver_variable": "discount_pct",
            "confidence_prior": 0.80
        })

        # 3. Shipping candidates
        candidates.append({
            "hypothesis_id": "HYP_SHI_01",
            "title": "Shipping fee cuts improve Conversion Rate",
            "description": "Lowering shipping fees reduces checkout cart abandonment and improves conversion rate.",
            "generated_from": "Historical Experiments",
            "affected_kpis": ["mean_conversion_rate", "total_orders"],
            "driver_variable": "shipping_fee",
            "confidence_prior": 0.65
        })
        candidates.append({
            "hypothesis_id": "HYP_SHI_02",
            "title": "High shipping charges increase cart abandonment",
            "description": "Fulfillment charges above benchmark limits drive drop-offs during the final checkout stage.",
            "generated_from": "Correlation Heuristics",
            "affected_kpis": ["mean_conversion_rate"],
            "driver_variable": "shipping_fee",
            "confidence_prior": 0.60
        })

        # 4. Marketing candidates
        candidates.append({
            "hypothesis_id": "HYP_MKT_01",
            "title": "Increasing marketing spend drives Traffic and Revenue",
            "description": "Allocating higher marketing budgets boosts customer acquisition and drives overall sales volume.",
            "generated_from": "SHAP Feature Importance",
            "affected_kpis": ["total_revenue"],
            "driver_variable": "marketing_spend",
            "confidence_prior": 0.70
        })
        candidates.append({
            "hypothesis_id": "HYP_MKT_02",
            "title": "Diminishing ROAS on elevated Marketing Spend",
            "description": "Scaling marketing budget beyond saturation thresholds results in lower return on advertising spend (ROAS).",
            "generated_from": "Sensitivity Analysis",
            "affected_kpis": ["total_profit"],
            "driver_variable": "marketing_spend",
            "confidence_prior": 0.60
        })

        # 5. Additional general templates to guarantee 10 candidates
        candidates.append({
            "hypothesis_id": "HYP_GEN_01",
            "title": "Sales declines are driven by Marketing budget cuts",
            "description": "Recent decreases in marketing allocation have led to lower incoming traffic and declining sales.",
            "generated_from": "SHAP Feature Importance",
            "affected_kpis": ["total_revenue"],
            "driver_variable": "marketing_spend",
            "confidence_prior": 0.55
        })
        candidates.append({
            "hypothesis_id": "HYP_GEN_02",
            "title": "Fulfillment fee hikes depress profit margin",
            "description": "An increase in fulfillment costs without a corresponding price increase directly reduces margins.",
            "generated_from": "Correlation Heuristics",
            "affected_kpis": ["total_profit"],
            "driver_variable": "shipping_fee",
            "confidence_prior": 0.50
        })

        # Filter candidates by keyword if they are related to query
        matched = []
        if "shipping" in q or "fee" in q:
            matched.extend([c for c in candidates if c["driver_variable"] == "shipping_fee"])
        if "discount" in q or "promo" in q:
            matched.extend([c for c in candidates if c["driver_variable"] == "discount_pct"])
        if "price" in q or "pricing" in q:
            matched.extend([c for c in candidates if c["driver_variable"] == "avg_selling_price"])
        if "marketing" in q or "spend" in q or "advertising" in q:
            matched.extend([c for c in candidates if c["driver_variable"] == "marketing_spend"])

        if matched:
            return matched
        return candidates

    def _score_candidate(
        self, 
        cand: Dict[str, Any], 
        shap_importance: List[Dict[str, Any]], 
        past_exps: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates a hypothesis candidate based on Data Support, Confidence, Impact, and Explainability.
        """
        driver = cand.get("driver_variable", "discount_pct")
        
        # 1. Data Support (SHAP feature alignment)
        data_support = 0.50
        for idx, feat in enumerate(shap_importance[:5]):
            if driver in feat["feature"]:
                data_support = 1.0 - (idx * 0.1) # Higher score for top SHAP features
                break

        # 2. Confidence (boosted by prior and past experiment success)
        confidence = cand.get("confidence_prior", 0.50)
        matching_past_exps = 0
        for exp in past_exps:
            if driver in exp.lower() or cand["title"].split(" ")[0].lower() in exp.lower():
                matching_past_exps += 1
        confidence_boost = min(0.30, matching_past_exps * 0.10)
        confidence = min(1.0, confidence + confidence_boost)

        # 3. Business Impact — data-driven using correlation signals
        trends = context.get("trends", {})
        revenue_trend = trends.get("revenue_trend", "stable")
        anomalies = context.get("anomalies", [])
        
        # Compute base impact from SHAP correlation alignment
        impact = 0.50
        for feat in shap_importance[:5]:
            if driver in feat.get("feature", ""):
                # Scale impact by the SHAP importance value (normalized)
                shap_val = abs(feat.get("importance_value", 0.0))
                impact = min(0.95, 0.50 + shap_val * 0.5)
                break
        
        # Boost for matching trend direction
        if revenue_trend == "decreasing" and driver in ("marketing_spend", "discount_pct"):
            impact = max(impact, 0.80)
        elif anomalies and driver == "shipping_fee":
            impact = 0.75

        # 4. Explainability
        # Based on structure and details of title + description
        explainability = 0.50
        desc_len = len(cand.get("description", ""))
        if desc_len > 100:
            explainability = 0.95
        elif desc_len > 50:
            explainability = 0.80

        # Composite score calculation
        composite_score = (data_support + confidence + impact + explainability) / 4.0

        return {
            "generator_score": round(composite_score, 4),
            "score_breakdown": {
                "data_support": round(data_support, 2),
                "confidence": round(confidence, 2),
                "impact": round(impact, 2),
                "explainability": round(explainability, 2)
            }
        }

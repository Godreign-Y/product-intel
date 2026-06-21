import os
import json
import re
import datetime
from typing import Dict, Any, List, Optional

from src.core.llm import LLMClient, get_llm_client
from src.utils.logger import setup_logger

logger = setup_logger("hypothesis_generator")

# Mappings for driver variable normalization
DRIVER_ALIASES = {
    "discount": "discount_pct",
    "discount %": "discount_pct",
    "discount percentage": "discount_pct",
    "discounts": "discount_pct",
    "discount_pct": "discount_pct",
    "promo": "discount_pct",
    "promotion": "discount_pct",
    
    "price": "avg_selling_price",
    "pricing": "avg_selling_price",
    "selling price": "avg_selling_price",
    "average price": "avg_selling_price",
    "avg price": "avg_selling_price",
    "avg_selling_price": "avg_selling_price",
    
    "shipping": "shipping_fee",
    "shipping fee": "shipping_fee",
    "fulfillment fee": "shipping_fee",
    "delivery fee": "shipping_fee",
    "shipping_fee": "shipping_fee",
    
    "marketing": "marketing_spend",
    "marketing spend": "marketing_spend",
    "ad spend": "marketing_spend",
    "ads": "marketing_spend",
    "spend": "marketing_spend",
    "advertising": "marketing_spend",
    "marketing_spend": "marketing_spend",

    "sales_channel_mix": "sales_channel_mix",
    "sales_channel": "sales_channel_mix",
    "sales channel": "sales_channel_mix",
    "channel": "sales_channel_mix",
    
    "campaign_mix": "campaign_mix",
    "campaign": "campaign_mix",
    
    "acquisition_mix": "acquisition_mix",
    "acquisition": "acquisition_mix",
    
    "inventory_available": "inventory_available",
    "inventory": "inventory_available",
    "stock": "inventory_available"
}

KPI_ALIASES = {
    "revenue": "revenue",
    "total_revenue": "revenue",
    "total revenue": "revenue",
    
    "profit": "profit",
    "total_profit": "profit",
    "total profit": "profit",
    "margin": "profit",
    
    "orders": "orders",
    "total_orders": "orders",
    "total orders": "orders",
    "sales volume": "orders",
    
    "conversion_rate": "conversion_rate",
    "mean_conversion_rate": "conversion_rate",
    "mean conversion rate": "conversion_rate",
    "conversion": "conversion_rate",
    "checkout": "conversion_rate",
    "ctr": "conversion_rate",
    
    "retention_rate": "retention_rate",
    "mean_retention_rate": "retention_rate",
    "mean retention rate": "retention_rate",
    "retention": "retention_rate"
}

def normalize_driver(driver: str) -> str:
    if not driver:
        return ""
    d_clean = driver.lower().replace("_", " ").strip()
    if driver.lower() in DRIVER_ALIASES:
        return DRIVER_ALIASES[driver.lower()]
    if d_clean in DRIVER_ALIASES:
        return DRIVER_ALIASES[d_clean]
    for k, v in DRIVER_ALIASES.items():
        if k in d_clean or d_clean in k:
            return v
    return driver.lower()

def normalize_kpi(kpi: str) -> str:
    if not kpi:
        return ""
    k_clean = kpi.lower().replace("_", " ").strip()
    if kpi.lower() in KPI_ALIASES:
        return KPI_ALIASES[kpi.lower()]
    if k_clean in KPI_ALIASES:
        return KPI_ALIASES[k_clean]
    for k, v in KPI_ALIASES.items():
        if k in k_clean or k_clean in k:
            return v
    return kpi.lower()

class HypothesisGenerator:
    def __init__(
        self, 
        db: Optional[Any] = None, 
        forecaster: Optional[Any] = None, 
        explainer: Optional[Any] = None, 
        history_manager: Optional[Any] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.db = db
        self.forecaster = forecaster
        self.explainer = explainer
        self.history_manager = history_manager
        self.llm_client = llm_client or get_llm_client()

        from src.core.history.embeddings.encoder import SentenceTransformerEncoder
        if history_manager and hasattr(history_manager, "encoder") and history_manager.encoder:
            self.encoder = history_manager.encoder
        else:
            self.encoder = SentenceTransformerEncoder()

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
        New prioritized hypothesis generator pipeline.
        Responsible for candidate generation, normalization, semantic deduplication, and prioritisation.
        """
        query = context.get("query", "")
        product_id = context.get("product_id", "P001")
        logger.info(f"generate_candidates: Starting refactored generation pipeline for query='{query}'")
        
        # 1. Parse target KPI
        target_kpi = self._determine_target_kpi(query)
        
        # 2. Retrieve SHAP values & past experiments
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
        kb_rules = self._get_knowledge_base_rules()
        kb_rules_summary = "\n".join([f"- {r}" for r in kb_rules[:5]])

        # 3. Generate raw candidates
        raw_candidates = self._generate_llm_candidates(
            query, target_kpi, shap_summary, past_exps_summary, kb_rules_summary, context
        )
        if not raw_candidates:
            raw_candidates = self._generate_fallback_candidates(query, target_kpi, context)

        # 4. Normalize & Filter candidates
        from src.core.decision.config_loader import load_decision_config
        try:
            cfg = load_decision_config()
            valid_drivers = list(cfg.get("elasticity", {}).get("min_driver_delta", {}).keys())
        except Exception:
            valid_drivers = []
        if not valid_drivers:
            valid_drivers = ["discount_pct", "shipping_fee", "avg_selling_price", "marketing_spend"]
            
        valid_kpis = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
        
        normalized_candidates = []
        for cand in raw_candidates:
            if not isinstance(cand, dict):
                continue
            
            # Reconcile id and hypothesis_id fields
            h_id = cand.get("hypothesis_id") or cand.get("id")
            if not h_id:
                continue
                
            title = cand.get("title")
            desc = cand.get("description")
            if not title or not desc:
                continue
                
            # Normalize driver_variable
            driver = normalize_driver(cand.get("driver_variable") or "")
            if driver not in valid_drivers:
                logger.warning(f"Discarding candidate '{h_id}': driver_variable '{driver}' not in configured drivers {valid_drivers}")
                continue
                
            # Normalize target KPI / affected KPIs list
            raw_kpis = cand.get("affected_kpis") or []
            if isinstance(raw_kpis, str):
                raw_kpis = [raw_kpis]
            kpis = [normalize_kpi(k) for k in raw_kpis]
            kpis = [k for k in kpis if k in valid_kpis]
            if not kpis:
                logger.warning(f"Discarding candidate '{h_id}': no valid affected_kpis in {raw_kpis}")
                continue
                
            normalized_cand = {
                "id": h_id,
                "hypothesis_id": h_id,
                "title": title,
                "description": desc,
                "driver_variable": driver,
                "affected_kpis": kpis,
                "confidence_prior": float(cand.get("confidence_prior") or 0.50),
                "generated_from": cand.get("generated_from") or "LLM Generation",
                "source": cand.get("source") or cand.get("generated_from") or "LLM"
            }
            normalized_candidates.append(normalized_cand)

        # 5. Semantic Deduplication (Similarity Threshold = 0.85)
        titles = [cand["title"] for cand in normalized_candidates]
        if len(titles) > 1 and hasattr(self, "encoder") and self.encoder:
            try:
                embeddings = [self.encoder.encode(t) for t in titles]
                import numpy as np
                norms = [np.linalg.norm(e) for e in embeddings]
                embeddings = [e / n if n > 1e-8 else e for e, n in zip(embeddings, norms)]
                
                keep_indices = []
                for i in range(len(normalized_candidates)):
                    is_duplicate = False
                    for j in keep_indices:
                        sim = float(np.dot(embeddings[i], embeddings[j]))
                        if sim >= 0.85:
                            is_duplicate = True
                            logger.info(f"Deduplication: Dropped '{titles[i]}' as similar to '{titles[j]}' (Similarity={sim:.3f})")
                            break
                    if not is_duplicate:
                        keep_indices.append(i)
                normalized_candidates = [normalized_candidates[idx] for idx in keep_indices]
            except Exception as ex:
                logger.error(f"Semantic deduplication failed: {ex}")

        # 6. Compute Evidence Coverage (SHAP, Query, Trend, Anomaly, Experiment)
        # Pre-query database for validated experiments matching target drivers
        validated_counts = {}
        successful_counts = {}
        if self.db:
            try:
                from src.core.history.storage.models import Experiment
                for driver in valid_drivers:
                    total_exp = self.db.query(Experiment).filter(
                        Experiment.driver == driver,
                        Experiment.outcome.in_(["positive", "negative"])
                    ).count()
                    wins = self.db.query(Experiment).filter(
                        Experiment.driver == driver,
                        Experiment.outcome == "positive"
                    ).count()
                    validated_counts[driver] = total_exp
                    successful_counts[driver] = wins
            except Exception as ex:
                logger.error(f"Failed pre-querying experiment history counts: {ex}")

        trends = context.get("trends", {})
        rev_trend = str(trends.get("revenue_trend", "stable")).lower()
        ord_trend = str(trends.get("order_trend", "stable")).lower()
        has_decline_trend = any("dec" in t or "decline" in t or "drop" in t or "down" in t for t in [rev_trend, ord_trend])
        has_decline_query = any(w in q_lower for w in ["decline", "drop", "decrease", "down", "why did"])
        anomalies = context.get("anomalies", [])
        has_checkout_anomaly = any(anom.get("kpi") in ["conversion_rate", "orders"] for anom in anomalies)

        scored_candidates = []
        for cand in normalized_candidates:
            driver = cand["driver_variable"]
            kpi = cand["affected_kpis"][0]
            
            # SHAP
            shap_features = self._get_shap_features(kpi)
            shap_match = any(driver in feat.get("feature", "") for feat in shap_features[:5])
            
            # User Query
            query_match = False
            for kw, drv in DRIVER_ALIASES.items():
                if drv == driver and kw in q_lower:
                    query_match = True
                    break
                    
            # Trend
            trend_match = False
            if (has_decline_trend or has_decline_query) and driver in ["marketing_spend", "discount_pct", "avg_selling_price"]:
                trend_match = True
                
            # Anomaly
            anomaly_match = False
            if has_checkout_anomaly and driver in ["shipping_fee", "discount_pct"]:
                anomaly_match = True
                
            # Past validated experiment
            exp_match = validated_counts.get(driver, 0) > 0
            
            evidence_sources = []
            if shap_match: evidence_sources.append("SHAP")
            if query_match: evidence_sources.append("UserQuery")
            if trend_match: evidence_sources.append("Trend")
            if anomaly_match: evidence_sources.append("Anomaly")
            if exp_match: evidence_sources.append("PastExperiment")
            
            coverage = len(evidence_sources) / 5.0
            
            # 7. Compute Historical Reliability
            total_exp = validated_counts.get(driver, 0)
            if total_exp > 0:
                reliability = successful_counts.get(driver, 0) / total_exp
            else:
                reliability = 0.50
                
            # 8. Compute User Intent Match
            explicit_drivers = []
            for kw, drv in DRIVER_ALIASES.items():
                if kw in q_lower:
                    if drv not in explicit_drivers:
                        explicit_drivers.append(drv)
            if explicit_drivers:
                if driver in explicit_drivers:
                    intent_match = 1.0
                elif driver == "marketing_spend" and "discount_pct" in explicit_drivers:
                    intent_match = 0.4
                elif driver == "discount_pct" and "marketing_spend" in explicit_drivers:
                    intent_match = 0.4
                else:
                    intent_match = 0.1
            else:
                intent_match = 1.0
                
            cand["evidence_sources"] = evidence_sources
            cand["evidence_coverage"] = float(coverage)
            cand["historical_reliability"] = float(reliability)
            cand["intent_match"] = float(intent_match)
            
            # Base priority score (excludes diversity bonus for initial sorting)
            cand["base_priority"] = 0.45 * coverage + 0.30 * reliability + 0.15 * intent_match
            scored_candidates.append(cand)

        # 9. Diversity Bonus (only the highest base priority per driver variable gets 1.0)
        scored_candidates.sort(key=lambda x: x["base_priority"], reverse=True)
        seen_drivers = set()
        for cand in scored_candidates:
            drv = cand["driver_variable"]
            if drv not in seen_drivers:
                cand["diversity_bonus"] = 1.0
                seen_drivers.add(drv)
            else:
                cand["diversity_bonus"] = 0.0

        # 10. Calculate Validation Priority (Clamped [0, 1])
        for cand in scored_candidates:
            priority = (
                0.45 * cand["evidence_coverage"] +
                0.30 * cand["historical_reliability"] +
                0.15 * cand["intent_match"] +
                0.10 * cand["diversity_bonus"]
            )
            cand["validation_priority"] = float(max(0.0, min(1.0, priority)))
            
            # Map backward compatible fields for downstream validators/rankers
            cand["is_primary"] = (cand["intent_match"] == 1.0)
            cand["generator_metadata"] = {
                "confidence_prior": cand["confidence_prior"],
                "generated_from": cand["generated_from"]
            }

        # 11. Final Rank & Return Top N (Default = 5)
        scored_candidates.sort(key=lambda x: x["validation_priority"], reverse=True)
        pruned_candidates = scored_candidates[:5]
        
        # Clean temporary sorting key
        for c in pruned_candidates:
            c.pop("base_priority", None)
            
        logger.info(f"generate_candidates: Finished candidate prioritisation. Returning top {len(pruned_candidates)} hypotheses.")
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
            "CRITICAL INSTRUCTIONS:\n"
            "1. Each hypothesis MUST directly address and explain the phenomenon described in the User Query (e.g., if the user asks why profit DECLINED, the hypotheses must frame the causal relationship explaining why profit declined, such as 'Marketing spend reduction caused profit decline' or 'Increased discounts eroded profitability').\n"
            "2. DO NOT output generic, textbook positive correlation statements like 'Marketing spend positively impacts revenue' or 'Average selling price affects profit'. The hypotheses must be actionable causal claims tailored to the query's direction.\n\n"
            "CONSTRAINT RULES:\n"
            "1. Each hypothesis MUST map to ONE of the following real database driver variables:\n"
            "   - 'discount_pct'\n"
            "   - 'shipping_fee'\n"
            "   - 'avg_selling_price'\n"
            "   - 'marketing_spend'\n"
            "2. Each hypothesis MUST list one or more affected KPIs from: ['total_revenue', 'total_profit', 'total_orders', 'mean_conversion_rate'].\n"
            "3. The returned JSON structure MUST be a list of objects containing exactly these fields:\n"
            "   - 'hypothesis_id': Unique identifier (e.g. 'HYP_DIS_01', 'HYP_PRI_02')\n"
            "   - 'title': Clear business statement explaining the cause of the phenomenon (e.g. 'Increased shipping charges drove down orders and profit')\n"
            "   - 'description': Multi-sentence description explaining the reasoning and connecting it to the query's specific metrics or direction\n"
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

        logger.info(f"_generate_llm_candidates: Requesting LLM with prompt length={len(user_prompt)}")
        try:
            raw_text = self.llm_client.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
                model_tier="capable",
            )
            logger.debug(f"_generate_llm_candidates: Raw LLM response received:\n{raw_text}")
            
            json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(raw_text)
                
            if isinstance(data, list) and len(data) >= 5:
                logger.info(f"_generate_llm_candidates: Extracted {len(data)} hypotheses from LLM successfully.")
                return data
            else:
                logger.warning(f"_generate_llm_candidates: Extracted data is not a valid list of size >= 5: {type(data)}")
        except Exception as e:
            logger.error(f"_generate_llm_candidates: LLM candidate hypothesis generation failed: {e}")
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

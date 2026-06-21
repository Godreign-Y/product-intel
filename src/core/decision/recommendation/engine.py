from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("recommendation_engine")

class RecommendationEngine:
    def __init__(self):
        cfg = load_decision_config()
        rec_cfg = cfg.get("recommendation", {})
        conf_thresh = cfg.get("confidence_thresholds", {})
        self.rollback_strategies = rec_cfg.get("rollback_strategies", {})
        self.immediate_rollout_threshold = conf_thresh.get("immediate_rollout", 0.75)
        logger.info(f"Initialized RecommendationEngine: immediate_rollout_threshold={self.immediate_rollout_threshold}")

    def generate_recommendations(
        self, 
        ranked_hypotheses: List[Dict[str, Any]],
        context_revenue: float = 0.0,
        db: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Translates prioritized hypotheses into actionable business recommendations.
        Now integrates causal estimates to output quantified revenue/profit shifts, historical success rates,
        confidence percentages, and risk categories.
        """
        logger.info(f"generate_recommendations: Translating {len(ranked_hypotheses)} ranked hypotheses into tactical recommendations. Context revenue={context_revenue}")
        recommendations = []
        for item in ranked_hypotheses:
            hypo = item["hypothesis"]
            val_res = item["validation"]
            conf_score = item["confidence"]
            rank_score = item["rank_score"]
            impact_pct = item["estimated_impact_pct"]
            
            title = hypo["title"]
            hyp_id = hypo["hypothesis_id"]
            
            # Map driver column based on hypothesis ID or keywords
            driver = "discount_pct"
            if "shi" in hyp_id.lower() or "shipping" in title.lower():
                driver = "shipping_fee"
            elif "pri" in hyp_id.lower() or "price" in title.lower() or "pricing" in title.lower():
                driver = "avg_selling_price"
            elif "spend" in title.lower() or "marketing" in title.lower():
                driver = "marketing_spend"

            # Determine Action Type
            action_type = "PRICING_ADJUSTMENT"
            if driver == "shipping_fee":
                action_type = "FULFILLMENT_OPTIMIZATION"
            elif driver == "marketing_spend":
                action_type = "BUDGET_REALLOCATION"
            elif driver == "discount_pct":
                action_type = "PROMOTIONAL_CAMPAIGN"
                
            logger.debug(f"generate_recommendations: Mapping '{hyp_id}' -> driver={driver}, action_type={action_type}")

            # Formulate text
            rec_text = f"Action recommendation for {title}: "
            if impact_pct > 0:
                rec_text += f"Proceed with implementation to capture an estimated +{impact_pct:.2f}% improvement in target KPI."
            else:
                rec_text += f"Review margin impacts carefully. Forecast simulation suggests a {impact_pct:.2f}% drop in gross metric."
                
            # Determine priority
            priority = "HIGH" if rank_score >= 0.65 else "MEDIUM" if rank_score >= 0.45 else "LOW"
            
            # Check if experiment is required (confidence is low)
            overall_conf = conf_score.get("overall_confidence", 0.5)
            needs_ab_test = overall_conf < self.immediate_rollout_threshold
            logger.debug(f"generate_recommendations: overall_confidence={overall_conf:.4f} vs threshold={self.immediate_rollout_threshold} -> needs_ab_test={needs_ab_test}")
            
            # Calculate estimated ROI proxy
            expected_delta = val_res.get("forecast_simulation", {}).get("expected_delta", 0.0)
            delta_pct = val_res.get("forecast_simulation", {}).get("delta_pct", 0.0)

            # Normalize ROI to dollar terms for non-revenue KPIs
            primary_kpi = hypo["affected_kpis"][0] if hypo.get("affected_kpis") else ""
            if "conversion" in primary_kpi and context_revenue > 0:
                estimated_roi = round((delta_pct / 100.0) * context_revenue, 2)
            else:
                estimated_roi = round(float(expected_delta), 2)
            logger.debug(f"generate_recommendations: Calculated ROI proxy={estimated_roi} (KPI={primary_kpi}, expected_delta={expected_delta})")

            # Calculate expected revenue and profit shifts
            expected_revenue_shift = 0.0
            expected_profit_shift = 0.0
            
            if "revenue" in primary_kpi:
                expected_revenue_shift = delta_pct
                if driver == "avg_selling_price":
                    expected_profit_shift = delta_pct * 1.2
                elif driver == "discount_pct":
                    expected_profit_shift = -delta_pct * 0.8
                elif driver == "marketing_spend":
                    expected_profit_shift = delta_pct * 0.5
                else:  # shipping_fee
                    expected_profit_shift = -delta_pct * 0.5
            elif "profit" in primary_kpi:
                expected_profit_shift = delta_pct
                if driver == "avg_selling_price":
                    expected_revenue_shift = delta_pct * 0.8
                elif driver == "discount_pct":
                    expected_revenue_shift = -delta_pct * 1.5
                elif driver == "marketing_spend":
                    expected_revenue_shift = delta_pct * 1.5
                else:  # shipping_fee
                    expected_revenue_shift = -delta_pct * 1.2
            else:  # conversion or orders
                expected_revenue_shift = delta_pct * 0.9
                expected_profit_shift = delta_pct * 0.8

            # Lookup historical success rate from database
            success_rate = 75.0
            if db:
                try:
                    logger.debug(f"generate_recommendations: Querying historical experiment success rate for driver={driver}")
                    from src.core.history.storage.models import Experiment
                    past_exps = db.query(Experiment).filter(Experiment.driver == driver).all()
                    if past_exps:
                        positives = sum(1 for e in past_exps if e.outcome == "positive")
                        success_rate = round((positives / len(past_exps)) * 100.0, 2)
                    else:
                        # Fallback query using type keyword
                        past_exps_type = db.query(Experiment).filter(Experiment.type.like(f"%{action_type[:5]}%")).all()
                        if past_exps_type:
                            positives = sum(1 for e in past_exps_type if e.outcome == "positive")
                            success_rate = round((positives / len(past_exps_type)) * 100.0, 2)
                except Exception as e:
                    logger.warning(f"generate_recommendations: Failed historical success rate query: {e}")
                    pass
            logger.debug(f"generate_recommendations: Determined historical success rate={success_rate}%")

            # Determine risk category
            from src.core.decision.recommendation.risk_classifier import risk_classifier
            volatility_val = "HIGH" if abs(delta_pct) > 15 else "MEDIUM" if abs(delta_pct) > 5 else "LOW"
            reversibility_val = "EASY" if action_type == "PROMOTIONAL_CAMPAIGN" else "MODERATE"
            risk_category = risk_classifier.classify(
                confidence=overall_conf,
                volatility=volatility_val,
                reversibility=reversibility_val
            )
            logger.info(f"generate_recommendations: Risk Category classification - Volatility: {volatility_val} (impact_pct={delta_pct:.2f}%), Confidence: {overall_conf:.4f} -> Resulting Risk Category: {risk_category} for hypothesis '{hyp_id}'")

            # Rich, action-specific rollback strategy from config
            rollback = self.rollback_strategies.get(
                action_type,
                f"Rollback {action_type.replace('_', ' ').lower()} settings to historical baselines if net margin drops below baseline control margins within 7 days."
            )
            if isinstance(rollback, str):
                rollback = rollback.strip()

            # Risk assessment structure
            risk_assessment = {
                "volatility": volatility_val,
                "reversibility": "EASY" if action_type == "PROMOTIONAL_CAMPAIGN" else "MODERATE",
                "data_confidence": round(overall_conf, 4),
                "impact_magnitude": round(abs(delta_pct), 2),
                "expected_revenue_shift_pct": round(expected_revenue_shift, 2),
                "expected_profit_shift_pct": round(expected_profit_shift, 2),
                "historical_success_rate_pct": round(success_rate, 2),
                "confidence_pct": round(overall_conf * 100.0, 2),
                "risk_category": risk_category
            }

            logger.info(f"generate_recommendations: Created recommendation for '{hyp_id}' (Priority={priority}, Needs A/B={needs_ab_test})")
            recommendations.append({
                "hypothesis_id": hyp_id,
                "recommendation_text": rec_text,
                "action_type": action_type,
                "expected_kpi_improvement": {
                    primary_kpi: f"{'+' if impact_pct > 0 else ''}{impact_pct:.2f}%",
                    "revenue_shift": f"{'+' if expected_revenue_shift > 0 else ''}{expected_revenue_shift:.2f}%",
                    "profit_shift": f"{'+' if expected_profit_shift > 0 else ''}{expected_profit_shift:.2f}%"
                } if primary_kpi else {},
                "expected_revenue_shift_pct": round(expected_revenue_shift, 2),
                "expected_profit_shift_pct": round(expected_profit_shift, 2),
                "historical_success_rate_pct": round(success_rate, 2),
                "confidence_pct": round(overall_conf * 100.0, 2),
                "risk_category": risk_category,
                "estimated_roi": estimated_roi,
                "priority": priority,
                "needs_experimentation": needs_ab_test,
                "rollback_strategy": rollback,
                "risk_assessment": risk_assessment,
                "confidence_score": overall_conf
            })
            
        logger.info(f"generate_recommendations: Successfully formulated {len(recommendations)} tactical recommendations.")
        return recommendations

from typing import Dict, Any, List

class RecommendationEngine:
    def __init__(self):
        pass

    def generate_recommendations(self, ranked_hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translates prioritized hypotheses into actionable business recommendations.
        """
        recommendations = []
        for item in ranked_hypotheses:
            hypo = item["hypothesis"]
            val_res = item["validation"]
            conf_score = item["confidence"]
            rank_score = item["rank_score"]
            impact_pct = item["estimated_impact_pct"]
            
            title = hypo["title"]
            hyp_id = hypo["hypothesis_id"]
            
            # Determine Action Type
            action_type = "PRICING_ADJUSTMENT"
            if "shipping" in hyp_id.lower() or "shipping" in title.lower():
                action_type = "FULFILLMENT_OPTIMIZATION"
            elif "spend" in title.lower() or "marketing" in title.lower():
                action_type = "BUDGET_REALLOCATION"
            elif "discount" in title.lower():
                action_type = "PROMOTIONAL_CAMPAIGN"
                
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
            needs_ab_test = overall_conf < 0.75
            
            # Calculate estimated ROI proxy (e.g. from forecast absolute delta)
            expected_delta = val_res.get("forecast_simulation", {}).get("expected_delta", 0.0)
            
            recommendations.append({
                "hypothesis_id": hyp_id,
                "recommendation_text": rec_text,
                "action_type": action_type,
                "expected_kpi_improvement": {hypo["affected_kpis"][0]: f"{'+' if impact_pct > 0 else ''}{impact_pct:.2f}%"},
                "estimated_roi": round(float(abs(expected_delta)), 2),
                "priority": priority,
                "needs_experimentation": needs_ab_test,
                "rollback_strategy": f"Rollback {action_type.replace('_', ' ').lower()} settings to historical baselines if net margin drops below baseline control margins within 7 days.",
                "confidence_score": overall_conf
            })
            
        return recommendations

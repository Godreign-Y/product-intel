import re
from typing import Dict, Any, List

class HypothesisGenerator:
    def __init__(self):
        pass

    def generate_candidates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates candidate hypotheses from query parsing and active business context.
        """
        query = context.get("query", "").lower()
        candidates = []
        
        # 1. Deduce from "shipping"
        if "shipping" in query or "fee" in query:
            candidates.append({
                "hypothesis_id": "HYP_SHI_01",
                "title": "Shipping fee cuts improve Conversion Rate",
                "description": "Reducing shipping fees lowers purchase friction, leading to a statistically significant rise in conversion rate, especially for budget customer segments.",
                "generated_from": "Historical Experiments",
                "affected_kpis": ["mean_conversion_rate", "total_orders"],
                "confidence_prior": 0.65
            })
            candidates.append({
                "hypothesis_id": "HYP_SHI_02",
                "title": "Lower shipping fees depress gross Profit Margins",
                "description": "Unless compensated by order volume, lowering shipping charges reduces gross margins since unit fulfillment costs remain constant.",
                "generated_from": "Sensitivity Analysis",
                "affected_kpis": ["total_profit"],
                "confidence_prior": 0.55
            })

        # 2. Deduce from "discount"
        if "discount" in query or "promo" in query:
            candidates.append({
                "hypothesis_id": "HYP_DIS_01",
                "title": "Higher discounts increase Order Volume",
                "description": "Increasing the average discount percentage drives a higher volume of purchases, particularly within category lines with elastic demand.",
                "generated_from": "Scenario Simulation",
                "affected_kpis": ["total_orders", "total_revenue"],
                "confidence_prior": 0.70
            })
            candidates.append({
                "hypothesis_id": "HYP_DIS_02",
                "title": "Excessive discounts erode net Profitability",
                "description": "Increasing discounts beyond the optimal elasticity boundary leads to gross margin decay that outweighs the volume gains.",
                "generated_from": "Sensitivity Analysis",
                "affected_kpis": ["total_profit"],
                "confidence_prior": 0.80
            })

        # 3. Deduce from "price" or "pricing"
        if "price" in query or "pricing" in query:
            candidates.append({
                "hypothesis_id": "HYP_PRI_01",
                "title": "Price increases decrease Customer Conversion",
                "description": "Increasing the average selling price of products creates price sensitivity and reduces checkout conversion rates.",
                "generated_from": "Sensitivity Analysis",
                "affected_kpis": ["mean_conversion_rate"],
                "confidence_prior": 0.75
            })
            candidates.append({
                "hypothesis_id": "HYP_PRI_02",
                "title": "Price elasticity of demand is category-dependent",
                "description": "Price sensitivity is highly active in Skincare/Haircare but passive in premium luxury categories.",
                "generated_from": "Historical Experiments",
                "affected_kpis": ["total_revenue", "mean_conversion_rate"],
                "confidence_prior": 0.60
            })

        # 4. Fallback/Default if no query terms match: deduce from active trends and anomalies
        if not candidates:
            # Let's inspect trends
            trends = context.get("trends", {})
            anomalies = context.get("anomalies", [])
            
            if trends.get("revenue_trend") == "decreasing" or "declined" in query or "drop" in query:
                candidates.append({
                    "hypothesis_id": "HYP_GEN_01",
                    "title": "Recent sales decline is driven by Marketing Spend cuts",
                    "description": "A drop in gross marketing spend has lowered daily traffic, resulting in reduced top-line revenue.",
                    "generated_from": "SHAP Feature Importance",
                    "affected_kpis": ["total_revenue"],
                    "confidence_prior": 0.50
                })
            
            if anomalies:
                candidates.append({
                    "hypothesis_id": "HYP_GEN_02",
                    "title": "Fulfillment failure is driving conversion drops",
                    "description": "A high statistical anomaly in order conversion matches operational log events related to shipping bottlenecks.",
                    "generated_from": "Anomaly Detection",
                    "affected_kpis": ["mean_conversion_rate", "total_orders"],
                    "confidence_prior": 0.55
                })
                
            # Always ensure at least one general baseline hypothesis
            if not candidates:
                candidates.append({
                    "hypothesis_id": "HYP_GEN_03",
                    "title": "Pricing updates are driving conversion shifts",
                    "description": "Changes in the average selling price over the last 30 days are correlated with shifts in checkout conversion.",
                    "generated_from": "Correlation Heuristics",
                    "affected_kpis": ["mean_conversion_rate"],
                    "confidence_prior": 0.50
                })
                
        return candidates

import pandas as pd
from typing import Dict, Any, List, Optional
from src.core.explainer import PredictionExplainer, get_clean_feature_name

class AnomalyExplainer:
    def __init__(self, prediction_explainer: PredictionExplainer):
        self.prediction_explainer = prediction_explainer

    def explain_anomaly(
        self,
        historical_df: pd.DataFrame,
        product_id: str,
        target_date: str,
        kpi: str,
        expected: float,
        actual: float,
        residual: float,
        percentage_change: float,
        triggered_rules: List[Dict[str, Any]],
        broken_relations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates detailed Root Cause Analysis (RCA) and explainability attributes for an anomaly.
        """
        top_drivers = []
        explanation_summary = ""
        
        # 1. Reuse SHAP explainability if a model is available for this KPI
        kpi_lower = kpi.lower()
        model_kpis = [m.lower() for m in self.prediction_explainer.forecaster.models.keys()]
        
        if kpi_lower in model_kpis:
            try:
                shap_result = self.prediction_explainer.explain_prediction(
                    historical_df=historical_df,
                    product_id=product_id,
                    target_metric=kpi_lower,
                    date=target_date
                )
                
                # Combine positive and negative drivers
                pos = shap_result.get("positive_drivers", [])
                neg = shap_result.get("negative_drivers", [])
                
                # Sort all contributions by absolute SHAP value
                all_contribs = sorted(pos + neg, key=lambda x: abs(x["shap_value"]), reverse=True)
                
                for c in all_contribs[:5]:
                    top_drivers.append({
                        "feature": get_clean_feature_name(c["feature"]),
                        "actual_value": round(float(c["actual_value"]), 4),
                        "shap_value": round(float(c["shap_value"]), 4),
                        "impact": "positive" if c["shap_value"] > 0 else "negative"
                    })
                    
                explanation_summary = shap_result.get("explanation_summary", "")
            except Exception as e:
                explanation_summary = f"Could not compute SHAP values for root cause: {str(e)}"
                
        # 2. Extract context from business rules
        rule_recs = []
        rule_explanations = []
        for rule in triggered_rules:
            rule_explanations.append(rule["business_explanation"])
            rule_recs.append(rule["recommended_action"])
            
        # 3. Extract context from broken relations
        relation_explanations = []
        for rel in broken_relations:
            relation_explanations.append(rel["details"])
            
        # 4. Generate Business Explanation & Recommendations if SHAP is not available
        if not explanation_summary:
            direction = "drop" if residual < 0 else "spike"
            explanation_summary = f"Detected {direction} of {abs(percentage_change):.1f}% in {kpi.replace('_', ' ').title()} relative to expected forecasts."
            
        # Formulate consolidated recommendation
        recommendations = []
        if rule_recs:
            recommendations.extend(rule_recs)
        else:
            # Default recommendations
            if residual < 0:
                if kpi_lower == "revenue" or kpi_lower == "orders":
                    recommendations.append("Inspect page traffic trends and checkout cart drop-off logs.")
                elif kpi_lower == "conversion_rate":
                    recommendations.append("Check payment integrations and checkout funnel loading times.")
                elif kpi_lower == "profit":
                    recommendations.append("Audit product manufacturing cost margins and shipping costs.")
            else:
                recommendations.append("Verify if a promotion, holiday seasonal spike, or marketing campaign was launched.")
                
        return {
            "anomaly_kpi": kpi.title(),
            "expected_value": round(expected, 4),
            "actual_value": round(actual, 4),
            "residual": round(residual, 4),
            "percentage_change": round(percentage_change, 2),
            "business_explanation": explanation_summary,
            "top_drivers": top_drivers,
            "triggered_rules_summary": rule_explanations,
            "broken_relations_summary": relation_explanations,
            "recommended_actions": list(set(recommendations))
        }

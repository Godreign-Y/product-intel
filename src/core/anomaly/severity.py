from typing import Dict, Any, List

class SeverityScorer:
    def __init__(self):
        pass

    def calculate_severity(
        self,
        residual_z_score: float,
        trend_z_score: float,
        multivariate_score: float,
        triggered_rules: List[Dict[str, Any]],
        broken_relations: List[Dict[str, Any]],
        change_point_confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates a final composite anomaly severity score between 0 and 100.
        Categorizes it into bands: Critical, High, Medium, Low, Informational.
        """
        # 1. Base score determined by rule severity (fail-safe checks)
        rule_base_score = 0.0
        rule_severity_map = {
            "CRITICAL": 85.0,
            "HIGH": 65.0,
            "MEDIUM": 45.0,
            "LOW": 25.0
        }
        
        for rule in triggered_rules:
            sev = rule.get("severity", "LOW").upper()
            score = rule_severity_map.get(sev, 25.0)
            if score > rule_base_score:
                rule_base_score = score
                
        # 2. Weighted components
        # Z-score contribution (capped at 4.0 as max deviation)
        z_contrib = min(100.0, abs(residual_z_score) * 25.0)
        
        # Trend Z-score contribution
        trend_contrib = min(100.0, abs(trend_z_score) * 25.0)
        
        # Relationship monitoring contribution
        relation_contrib = 100.0 if len(broken_relations) > 0 else 0.0
        
        # Change point confidence contribution
        cp_contrib = change_point_confidence * 100.0
        
        # Weighting Schema:
        # Residual Z-score: 30%
        # Trend Z-score: 15%
        # Multivariate Score: 20%
        # Relationships: 15%
        # Change Point: 10%
        # Rule Violations: 10%
        
        composite_score = (
            0.30 * z_contrib +
            0.15 * trend_contrib +
            0.20 * multivariate_score +
            0.15 * relation_contrib +
            0.10 * cp_contrib +
            0.10 * (100.0 if len(triggered_rules) > 0 else 0.0)
        )
        
        # Override with rule baseline if rule baseline is higher
        final_score = max(composite_score, rule_base_score)
        final_score = min(100.0, max(0.0, final_score))
        
        # Categorize
        if final_score >= 80.0:
            status = "Critical"
        elif final_score >= 60.0:
            status = "High"
        elif final_score >= 40.0:
            status = "Medium"
        elif final_score >= 20.0:
            status = "Low"
        else:
            status = "Informational"
            
        return {
            "severity_score": round(final_score, 2),
            "status": status,
            "components": {
                "residual_z_contrib": round(z_contrib, 2),
                "trend_z_contrib": round(trend_contrib, 2),
                "multivariate_score": round(multivariate_score, 2),
                "relationship_drift_score": round(relation_contrib, 2),
                "change_point_score": round(cp_contrib, 2),
                "business_rules_triggered": len(triggered_rules)
            }
        }

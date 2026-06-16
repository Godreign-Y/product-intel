from typing import Dict, Any, List, Optional

class ConfidenceScorer:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Default configurable weights summing to 1.0
        self.weights = weights or {
            "historical": 0.15,
            "correlation": 0.20,
            "sensitivity": 0.20,
            "forecast": 0.25,
            "causal": 0.20
        }

    def compute_confidence(
        self, 
        validation_results: Dict[str, Any], 
        historical_evidence: List[Dict[str, Any]],
        title: str
    ) -> Dict[str, Any]:
        """
        Calculates the overall confidence score and a breakdown.
        """
        # 1. Historical Agreement
        hist_score = 0.5
        if historical_evidence:
            # Check if previous trials had positive outcome
            matches = [e for e in historical_evidence if e.get("outcome") == "positive"]
            if matches:
                hist_score = 0.90
            else:
                hist_score = 0.60
                
        # 2. Correlation Score
        corr = validation_results.get("correlation", {})
        pearson = abs(corr.get("pearson", 0.0))
        spearman = abs(corr.get("spearman", 0.0))
        corr_score = round(float((pearson + spearman) / 2.0), 4)
        # Minimum baseline for correlation relevance
        corr_score = max(0.10, min(1.00, corr_score))

        # 3. Sensitivity Score
        sens = validation_results.get("sensitivity", {})
        elasticity = abs(sens.get("elasticity_score", 0.0))
        # Map elasticity magnitude to score
        sens_score = min(1.0, elasticity * 2.0)
        sens_score = max(0.10, sens_score)

        # 4. Forecast Simulation Score
        f_sim = validation_results.get("forecast_simulation", {})
        delta_pct = f_sim.get("delta_pct", 0.0)
        
        # Check direction alignment
        is_pos_hypo = "increase" in title.lower() or "improve" in title.lower() or "rise" in title.lower() or "up" in title.lower()
        is_neg_hypo = "decrease" in title.lower() or "drop" in title.lower() or "lower" in title.lower() or "down" in title.lower() or "reduce" in title.lower()
        
        aligned = True
        if is_pos_hypo and delta_pct < 0:
            aligned = False
        elif is_neg_hypo and delta_pct > 0:
            aligned = False
            
        if aligned:
            # Map percentage change to a bounded 0-1 score
            fore_score = min(1.0, abs(delta_pct) / 2.0)
            fore_score = max(0.20, fore_score)  # baseline fallback
        else:
            fore_score = 0.10  # penalty for contradiction

        # 5. Causal Score
        causal = validation_results.get("causal", {})
        p_val = causal.get("p_value", 1.0)
        causal_score = round(float(1.0 - p_val), 4)
        causal_score = max(0.10, causal_score)

        # Calculate weighted sum
        overall = (
            self.weights["historical"] * hist_score +
            self.weights["correlation"] * corr_score +
            self.weights["sensitivity"] * sens_score +
            self.weights["forecast"] * fore_score +
            self.weights["causal"] * causal_score
        )
        
        overall = round(min(0.99, max(0.10, overall)), 4)
        
        return {
            "overall_confidence": overall,
            "breakdown": {
                "historical_agreement": round(hist_score, 4),
                "correlation_strength": round(corr_score, 4),
                "sensitivity_alignment": round(sens_score, 4),
                "forecast_simulation_agreement": round(fore_score, 4),
                "causal_confidence": round(causal_score, 4)
            },
            "reasoning": f"Overall confidence score of {overall:.2f} is supported by causal p-value verification ({1-p_val:.2f}) and simulated forecaster alignment."
        }

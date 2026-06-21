from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config

class ConfidenceScorer:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        cfg = load_decision_config()
        conf_cfg = cfg.get("confidence", {})
        # Load weights from config, with fallback defaults
        self.weights = weights or conf_cfg.get("weights", {
            "historical": 0.15,
            "correlation": 0.20,
            "sensitivity": 0.20,
            "forecast": 0.25,
            "causal": 0.20
        })

    def compute_confidence(
        self, 
        validation_results: Dict[str, Any], 
        historical_evidence: List[Dict[str, Any]],
        title: str,
        product_df_len: int = 0
    ) -> Dict[str, Any]:
        """
        Calculates the overall confidence score using a normalized 0-100 composite scoring system.
        """
        # 1. Historical Agreement (Scaled 0-100)
        hist_score = 50.0
        if historical_evidence:
            matches = [e for e in historical_evidence if e.get("outcome") == "positive"]
            if matches:
                hist_score = 90.0
            else:
                hist_score = 60.0
                
        # 2. Correlation Score (Scaled 0-100)
        corr = validation_results.get("correlation", {})
        pearson = abs(corr.get("pearson", 0.0))
        spearman = abs(corr.get("spearman", 0.0))
        corr_score = round(float((pearson + spearman) / 2.0 * 100.0), 2)
        corr_score = max(10.0, min(100.0, corr_score))

        # 3. Sensitivity Score / Effect Size (Scaled 0-100)
        sens = validation_results.get("sensitivity", {})
        elasticity = abs(sens.get("elasticity_score", 0.0))
        sens_score = round(min(100.0, elasticity * 2.0 * 100.0), 2)
        sens_score = max(10.0, sens_score)

        # 4. Forecast Simulation Score (Scaled 0-100)
        f_sim = validation_results.get("forecast_simulation", {})
        delta_pct = f_sim.get("delta_pct", 0.0)
        
        is_pos_hypo = "increase" in title.lower() or "improve" in title.lower() or "rise" in title.lower() or "up" in title.lower()
        is_neg_hypo = "decrease" in title.lower() or "drop" in title.lower() or "lower" in title.lower() or "down" in title.lower() or "reduce" in title.lower()
        
        aligned = True
        if is_pos_hypo and delta_pct < 0:
            aligned = False
        elif is_neg_hypo and delta_pct > 0:
            aligned = False
            
        if aligned:
            fore_score = round(min(100.0, abs(delta_pct) / 2.0 * 100.0), 2)
            fore_score = max(20.0, fore_score)
        else:
            fore_score = 10.0  # penalty for contradiction

        # 5. Causal Score / Statistical Confidence (Scaled 0-100)
        causal = validation_results.get("causal", {})
        p_val = causal.get("p_value", 1.0)
        causal_score = round(float((1.0 - p_val) * 100.0), 2)
        causal_score = max(10.0, causal_score)

        # Calculate weighted average of normalized 0-100 scores
        overall_100 = (
            self.weights["historical"] * hist_score +
            self.weights["correlation"] * corr_score +
            self.weights["sensitivity"] * sens_score +
            self.weights["forecast"] * fore_score +
            self.weights["causal"] * causal_score
        )
        
        # Scale back to 0.0 - 1.0 standard decimal for API and Database compatibilities
        overall = round(min(0.99, max(0.10, overall_100 / 100.0)), 4)

        # Compute data quality factor (0.0 to 1.0)
        data_quality_factor = 0.0
        if product_df_len > 0:
            data_quality_factor = round(min(1.0, product_df_len / 365.0), 4)

        # Build dynamic reasoning identifying the dominant signal
        signal_contributions = {
            "Historical Agreement": self.weights["historical"] * hist_score,
            "Correlation Strength": self.weights["correlation"] * corr_score,
            "Sensitivity Alignment": self.weights["sensitivity"] * sens_score,
            "Forecast Simulation Agreement": self.weights["forecast"] * fore_score,
            "Causal Confidence": self.weights["causal"] * causal_score
        }
        dominant_signal = max(signal_contributions, key=signal_contributions.get)
        dominant_value = signal_contributions[dominant_signal]

        reasoning = (
            f"Confidence driven primarily by {dominant_signal} "
            f"(weighted contribution: {dominant_value:.2f}%). "
        )
        if p_val < 0.05:
            reasoning += f"Causal p-value of {p_val:.3f} provides strong statistical validation. "
        elif p_val < 0.10:
            reasoning += f"Causal p-value of {p_val:.3f} provides moderate statistical support. "
        else:
            reasoning += f"Causal p-value of {p_val:.3f} is not statistically significant; interpret with caution. "

        if data_quality_factor >= 0.8:
            reasoning += f"Data coverage is excellent ({product_df_len} days)."
        elif data_quality_factor >= 0.5:
            reasoning += f"Data coverage is moderate ({product_df_len} days)."
        elif product_df_len > 0:
            reasoning += f"Data coverage is limited ({product_df_len} days); confidence may improve with more history."

        return {
            "overall_confidence": overall,
            "data_quality_factor": data_quality_factor,
            "breakdown": {
                "historical_agreement": round(hist_score, 2),
                "correlation_strength": round(corr_score, 2),
                "sensitivity_alignment": round(sens_score, 2),
                "forecast_simulation_agreement": round(fore_score, 2),
                "causal_confidence": round(causal_score, 2)
            },
            "reasoning": reasoning.strip()
        }


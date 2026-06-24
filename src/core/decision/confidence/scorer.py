from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("confidence_scorer")

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
        logger.info(f"Initialized ConfidenceScorer with weights: {self.weights}")

    def compute_confidence(
        self, 
        validation_results: Dict[str, Any], 
        historical_evidence: List[Dict[str, Any]],
        title: str,
        product_df_len: int = 0,
        driver_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates the overall confidence score using a normalized 0-100 composite scoring system.
        """
        from src.core.decision.direction_utils import parse_hypothesis_direction

        logger.info(f"compute_confidence: Scoring confidence for hypothesis='{title}' with data coverage of {product_df_len} days.")
        
        # 1. Historical Agreement (Scaled 0-100)
        hist_score = 50.0
        if historical_evidence:
            matches = [e for e in historical_evidence if e.get("outcome") == "positive"]
            if matches:
                hist_score = 90.0
            else:
                hist_score = 60.0
        logger.debug(f"compute_confidence: Historical score={hist_score} (evidence_count={len(historical_evidence)})")
                
        # 2. Correlation Score (Scaled 0-100) — includes MI when linear correlation is weak
        corr = validation_results.get("correlation", {})
        pearson = abs(corr.get("pearson", 0.0))
        spearman = abs(corr.get("spearman", 0.0))
        mi = abs(corr.get("mi_score", 0.0))
        linear_corr = (pearson + spearman) / 2.0
        corr_strength = max(linear_corr, mi * 0.5) if mi > linear_corr else linear_corr
        corr_score = round(float(corr_strength * 100.0), 2)
        corr_score = max(10.0, min(100.0, corr_score))
        logger.debug(f"compute_confidence: Correlation score={corr_score} (Pearson={pearson:.4f}, Spearman={spearman:.4f})")

        # 3. Sensitivity Score / Effect Size (Scaled 0-100)
        sens = validation_results.get("sensitivity", {})
        elasticity = abs(sens.get("elasticity_score", 0.0))
        sens_score = round(min(100.0, elasticity * 2.0 * 100.0), 2)
        sens_score = max(10.0, sens_score)
        logger.debug(f"compute_confidence: Sensitivity score={sens_score} (Elasticity={elasticity:.4f})")

        # 4. Forecast Simulation Score (Scaled 0-100)
        f_sim = validation_results.get("forecast_simulation", {})
        delta_pct = f_sim.get("delta_pct", 0.0)
        forecast_sig = validation_results.get("signals", {}).get("forecast", {})

        if not driver_keyword:
            driver_keyword = validation_results.get("driver_key") or driver_keyword
        if not driver_keyword:
            title_lower = title.lower()
            if "shipping" in title_lower or "fee" in title_lower:
                driver_keyword = "shipping"
            elif "price" in title_lower or "pricing" in title_lower:
                driver_keyword = "price"
            elif "marketing" in title_lower or "spend" in title_lower:
                driver_keyword = "marketing"
            else:
                driver_keyword = "discount"

        hypo_dir = parse_hypothesis_direction(title, driver_keyword or "discount")
        
        aligned = True
        if forecast_sig.get("direction_match") is False:
            aligned = False
            fore_score = 10.0
        elif forecast_sig.get("direction_match") is True:
            fore_score = round(min(100.0, abs(delta_pct) / 2.0 * 100.0), 2)
            fore_score = max(20.0, fore_score)
        elif hypo_dir == "neutral":
            fore_score = 50.0  # moderate default score to penalize ambiguous phrasing
        elif hypo_dir == "positive" and delta_pct < 0:
            aligned = False
            fore_score = 10.0  # penalty for contradiction
        elif hypo_dir == "negative" and delta_pct > 0:
            aligned = False
            fore_score = 10.0  # penalty for contradiction
        else:
            fore_score = round(min(100.0, abs(delta_pct) / 2.0 * 100.0), 2)
            fore_score = max(20.0, fore_score)
            
        logger.debug(f"compute_confidence: Forecast score={fore_score} (delta_pct={delta_pct}%, hypo_dir={hypo_dir}, aligned={aligned})")

        # 5. Causal Score / Statistical Confidence (Scaled 0-100)
        causal = validation_results.get("causal", {})
        p_val = causal.get("p_value", 1.0)
        causal_score = round(float((1.0 - p_val) * 100.0), 2)
        causal_score = max(10.0, causal_score)
        logger.debug(f"compute_confidence: Causal score={causal_score} (p_value={p_val:.4f})")

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

        adjudication = validation_results.get("adjudication", {})
        if adjudication:
            verdict = adjudication.get("verdict", "inconclusive")
            family_agreement = float(adjudication.get("family_agreement", 0.0))
            if verdict == "supported":
                overall = min(0.99, overall + 0.05 * family_agreement)
            elif verdict == "contradicted":
                overall = max(0.10, overall * 0.55)
            else:
                overall = max(0.10, overall * 0.88)
            overall = round(overall, 4)

        logger.info(f"compute_confidence: Weighted sum={overall_100:.2f} -> overall_confidence={overall}")

        # Compute data quality factor (0.0 to 1.0)
        data_quality_factor = 0.0
        if product_df_len > 0:
            data_quality_factor = round(min(1.0, product_df_len / 365.0), 4)
        logger.debug(f"compute_confidence: data_quality_factor={data_quality_factor}")

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
        if adjudication:
            reasoning = adjudication.get("summary", reasoning) + " "
            reasoning += f"Validation verdict: {adjudication.get('verdict')} ({adjudication.get('confidence_band')} confidence band). "
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

        logger.info(f"compute_confidence: Finished scoring confidence. Reasoning: '{reasoning.strip()}'")
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
            "reasoning": reasoning.strip(),
            "validation_verdict": adjudication.get("verdict") if adjudication else None,
            "validation_confidence_band": adjudication.get("confidence_band") if adjudication else None,
        }

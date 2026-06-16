from typing import Dict, Any, List

class HypothesisRanker:
    def __init__(self):
        pass

    def rank_hypotheses(
        self, 
        hypotheses: List[Dict[str, Any]], 
        validation_results: Dict[str, Dict[str, Any]], 
        confidence_scores: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ranks hypotheses by sorting them on a composite score of confidence and business impact.
        """
        ranked = []
        for hypo in hypotheses:
            hyp_id = hypo["hypothesis_id"]
            val_res = validation_results.get(hyp_id, {})
            conf_score = confidence_scores.get(hyp_id, {})
            
            overall_conf = conf_score.get("overall_confidence", 0.5)
            
            # Extract impact from forecast delta pct
            delta_pct = val_res.get("forecast_simulation", {}).get("delta_pct", 0.0)
            impact_score = min(1.0, abs(delta_pct) / 10.0)  # Bound to 0-1 range
            
            # Composite rank score
            rank_score = round(float(0.5 * overall_conf + 0.5 * impact_score), 4)
            
            ranked.append({
                "hypothesis": hypo,
                "validation": val_res,
                "confidence": conf_score,
                "rank_score": rank_score,
                "estimated_impact_pct": delta_pct
            })
            
        # Sort descending
        ranked = sorted(ranked, key=lambda x: x["rank_score"], reverse=True)
        return ranked

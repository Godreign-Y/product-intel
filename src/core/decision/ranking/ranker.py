from typing import Dict, Any, List

from src.core.decision.config_loader import load_decision_config

class HypothesisRanker:
    def __init__(self):
        cfg = load_decision_config()
        rank_cfg = cfg.get("ranking", {}).get("weights", {})
        self.w_confidence = rank_cfg.get("confidence", 0.60)
        self.w_impact = rank_cfg.get("impact", 0.40)
        self.business_objectives = cfg.get("business_objectives", {
            "profit": 0.40,
            "revenue": 0.25,
            "orders": 0.15,
            "retention": 0.10,
            "conversion": 0.10
        })

    def rank_hypotheses(
        self, 
        hypotheses: List[Dict[str, Any]], 
        validation_results: Dict[str, Dict[str, Any]], 
        confidence_scores: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ranks hypotheses by a configurable weighted composite of confidence and business impact.
        Uses batch-normalized impact scores scaled by dynamic business objectives weights, and tie-breaking by causal ATE magnitude.
        """
        # Pre-compute max delta across the batch for normalization
        all_deltas = []
        for hypo in hypotheses:
            hyp_id = hypo["hypothesis_id"]
            val_res = validation_results.get(hyp_id, {})
            delta_pct = val_res.get("forecast_simulation", {}).get("delta_pct", 0.0)
            all_deltas.append(abs(delta_pct))
        max_delta = max(all_deltas) if all_deltas else 1.0
        max_delta = max(max_delta, 1.0)  # prevent division by zero

        ranked = []
        for hypo in hypotheses:
            hyp_id = hypo["hypothesis_id"]
            val_res = validation_results.get(hyp_id, {})
            conf_score = confidence_scores.get(hyp_id, {})
            
            overall_conf = conf_score.get("overall_confidence", 0.5)
            
            # Batch-normalized impact score instead of fixed /10.0 cap
            delta_pct = val_res.get("forecast_simulation", {}).get("delta_pct", 0.0)
            base_impact = abs(delta_pct) / max_delta
            
            # Determine target KPI to look up business objective weight
            affected_kpis = hypo.get("affected_kpis", ["revenue"])
            kpi_primary = affected_kpis[0].lower() if affected_kpis else "revenue"
            
            obj_key = "revenue"
            if "profit" in kpi_primary:
                obj_key = "profit"
            elif "revenue" in kpi_primary:
                obj_key = "revenue"
            elif "order" in kpi_primary:
                obj_key = "orders"
            elif "retention" in kpi_primary:
                obj_key = "retention"
            elif "conversion" in kpi_primary:
                obj_key = "conversion"
                
            kpi_weight = self.business_objectives.get(obj_key, 0.20)
            impact_score = base_impact * kpi_weight
            
            # Configurable weighted composite rank score
            rank_score = round(float(self.w_confidence * overall_conf + self.w_impact * impact_score), 4)

            # Store causal ATE for tie-breaking
            ate_magnitude = abs(val_res.get("causal", {}).get("ate_estimate", 0.0))
            
            ranked.append({
                "hypothesis": hypo,
                "validation": val_res,
                "confidence": conf_score,
                "rank_score": rank_score,
                "estimated_impact_pct": delta_pct,
                "_ate_magnitude": ate_magnitude
            })
            
        # Sort descending by rank_score, tie-break by causal ATE magnitude
        ranked = sorted(ranked, key=lambda x: (x["rank_score"], x["_ate_magnitude"]), reverse=True)

        # Clean internal tie-breaking field from output
        for item in ranked:
            item.pop("_ate_magnitude", None)

        return ranked

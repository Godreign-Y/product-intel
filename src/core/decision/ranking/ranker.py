from typing import Dict, Any, List

from src.core.decision.config_loader import load_decision_config
from src.core.decision.validation.adjudicator import verdict_rank_multiplier
from src.utils.logger import setup_logger

logger = setup_logger("hypothesis_ranker")

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
        logger.info(f"Initialized HypothesisRanker: confidence_weight={self.w_confidence}, impact_weight={self.w_impact}, objectives_weights={self.business_objectives}")

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
        logger.info(f"rank_hypotheses: Starting prioritization and ranking of {len(hypotheses)} candidate hypotheses.")
        
        # Pre-compute max delta across the batch for normalization
        all_deltas = []
        for hypo in hypotheses:
            hyp_id = hypo["hypothesis_id"]
            val_res = validation_results.get(hyp_id, {})
            delta_pct = val_res.get("forecast_simulation", {}).get("delta_pct", 0.0)
            all_deltas.append(abs(delta_pct))
        max_delta = max(all_deltas) if all_deltas else 1.0
        max_delta = max(max_delta, 1.0)  # prevent division by zero
        logger.debug(f"rank_hypotheses: Batch max forecast delta={max_delta}% for normalization.")
 
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

            adjudication = val_res.get("adjudication", {})
            verdict = adjudication.get("verdict", "inconclusive")
            rank_score = round(rank_score * verdict_rank_multiplier(verdict), 4)

            # Store causal ATE for tie-breaking
            ate_magnitude = abs(val_res.get("causal", {}).get("ate_estimate", 0.0))
            
            logger.debug(f"rank_hypotheses: Scoring '{hyp_id}': title='{hypo.get('title')}'")
            logger.debug(f"  overall_conf={overall_conf:.4f}, base_impact={base_impact:.4f}, objective_weight={kpi_weight} ({obj_key})")
            logger.debug(f"  weighted composite rank_score={rank_score:.4f}, causal_ATE_tiebreaker={ate_magnitude:.4f}")
            
            # Evaluate and log risk category / volatility profile
            from src.core.decision.recommendation.risk_classifier import risk_classifier
            v_val = "HIGH" if abs(delta_pct) > 15 else "MEDIUM" if abs(delta_pct) > 5 else "LOW"
            r_cat = risk_classifier.classify(
                confidence=overall_conf,
                volatility=v_val,
                reversibility="EASY" if obj_key == "conversion" else "MODERATE"
            )
            logger.info(f"rank_hypotheses: Analyzed risk profile for '{hyp_id}' -> Volatility: {v_val} (impact_pct={delta_pct:.2f}%), Confidence: {overall_conf:.4f} -> Projected Risk: {r_cat}")
            
            ranked.append({
                "hypothesis": hypo,
                "validation": val_res,
                "confidence": conf_score,
                "rank_score": rank_score,
                "estimated_impact_pct": delta_pct,
                "validation_verdict": verdict,
                "validation_confidence_band": adjudication.get("confidence_band"),
                "_ate_magnitude": ate_magnitude,
                "_verdict_sort": {"supported": 0, "inconclusive": 1, "contradicted": 2}.get(verdict, 1),
            })
            
        # Sort descending by rank_score (prioritizing primary opportunities), tie-break by causal ATE magnitude
        logger.info("rank_hypotheses: Sorting ranked hypotheses prioritizing primary opportunities first.")
        ranked = sorted(
            ranked,
            key=lambda x: (
                not x["hypothesis"].get("is_primary", True),
                x["_verdict_sort"],
                -x["rank_score"],
                -x["_ate_magnitude"],
            ),
        )

        # Clean internal tie-breaking fields from output
        for item in ranked:
            item.pop("_ate_magnitude", None)
            item.pop("_verdict_sort", None)

        logger.info(f"rank_hypotheses: Rank sorting complete. Highest priority hypothesis: '{ranked[0]['hypothesis']['hypothesis_id']}' with score={ranked[0]['rank_score']:.4f}")
        return ranked

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from src.core.history.manager import HistoryManager
from src.core.decision.config_loader import load_decision_config

class EvidenceRetriever:
    def __init__(self, db: Session, history_manager: Optional[HistoryManager] = None):
        self.db = db
        # Reuse existing HistoryManager to avoid duplicating search code
        self.history_manager = history_manager or HistoryManager(db)
        cfg = load_decision_config()
        ev_cfg = cfg.get("evidence", {})
        self.search_limit = ev_cfg.get("search_limit", 5)
        self.kpi_match_bonus = ev_cfg.get("kpi_match_bonus", 0.10)

    def retrieve_historical_evidence(self, query: str, affected_kpis: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves matching historical experiments and outputs supporting evidence details.
        Now builds an enriched query using affected_kpis and applies a KPI match bonus.
        """
        # Build enriched query that includes KPI context for better semantic search
        kpi_str = ", ".join(affected_kpis) if affected_kpis else ""
        enriched_query = f"{query} affecting {kpi_str}" if kpi_str else query

        # Search the vector index for similar past reports (config-driven limit)
        search_results = self.history_manager.semantic_search(enriched_query, limit=self.search_limit)
        
        evidence_list = []
        for item in search_results:
            exp = item["experiment"]
            rep = item["report"]
            score = item["score"]
            
            # Apply KPI match bonus: boost similarity when evidence experiment
            # relates to the same KPIs the hypothesis affects
            if affected_kpis and exp.change_summary:
                summary_lower = exp.change_summary.lower()
                for kpi in affected_kpis:
                    if kpi.lower().replace("total_", "").replace("mean_", "") in summary_lower:
                        score = min(1.0, score + self.kpi_match_bonus)
                        break
            
            # Formulate evidence item
            evidence_list.append({
                "experiment_id": exp.experiment_id,
                "type": exp.type,
                "outcome": exp.outcome,
                "improvement_pct": exp.improvement_pct,
                "change_summary": exp.change_summary,
                "learnings": rep.structured_json.get("learnings", "") if rep.structured_json else "",
                "recommendations": rep.structured_json.get("recommendations", "") if rep.structured_json else "",
                "semantic_similarity": score
            })
        
        # Re-sort by boosted similarity scores
        evidence_list.sort(key=lambda x: x["semantic_similarity"], reverse=True)
            
        return evidence_list

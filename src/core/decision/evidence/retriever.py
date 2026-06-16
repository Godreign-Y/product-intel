from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from src.core.history.manager import HistoryManager

class EvidenceRetriever:
    def __init__(self, db: Session, history_manager: Optional[HistoryManager] = None):
        self.db = db
        # Reuse existing HistoryManager to avoid duplicating search code
        self.history_manager = history_manager or HistoryManager(db)

    def retrieve_historical_evidence(self, query: str, affected_kpis: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves matching historical experiments and outputs supporting evidence details.
        """
        # Search the vector index for similar past reports
        search_results = self.history_manager.semantic_search(query, limit=3)
        
        evidence_list = []
        for item in search_results:
            exp = item["experiment"]
            rep = item["report"]
            score = item["score"]
            
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
            
        return evidence_list

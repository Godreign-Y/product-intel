import pandas as pd
import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.core.history.storage.database import engine, Base
from src.core.history.storage.models import Snapshot, Event, Experiment, Report, ReportEmbedding
from src.core.decision.storage.models import DecisionContext, Hypothesis, ValidationResult, ConfidenceScore, Recommendation, ExperimentPlan
from src.core.history.builders.snapshot import SnapshotBuilder
from src.core.history.detectors.event import EventDetector
from src.core.history.detectors.experiment import ExperimentDetector
from src.core.history.reports.generator import ReportGenerator
from src.core.history.embeddings.encoder import SentenceTransformerEncoder
from src.core.history.retrievers.similarity import SimilarityRetriever
from src.utils.logger import setup_logger

logger = setup_logger("history_manager")

class HistoryManager:
    def __init__(self, db: Session, encoder: Optional[SentenceTransformerEncoder] = None):
        self.db = db
        self.encoder = encoder or SentenceTransformerEncoder()
        self.retriever = SimilarityRetriever(db, self.encoder)
        self.snapshot_builder = SnapshotBuilder()
        self.event_detector = EventDetector()
        self.experiment_detector = ExperimentDetector()
        self.report_generator = ReportGenerator()

    def rebuild_tables(self):
        """
        Cleans and recreates the historical intelligence repository tables
        without dropping the raw product_performance dataset.
        """
        from src.core.history.storage.models import Snapshot, Event, Experiment, Report, ReportEmbedding, KnowledgeBase
        
        logger.info("Dropping historical repository tables selectively...")
        tables = [
            ReportEmbedding.__table__,
            Report.__table__,
            Experiment.__table__,
            Event.__table__,
            Snapshot.__table__,
            KnowledgeBase.__table__
        ]
        for table in tables:
            table.drop(bind=engine, checkfirst=True)
            
        logger.info("Creating historical repository tables selectively...")
        for table in reversed(tables):
            table.create(bind=engine, checkfirst=True)
            
        logger.info("Database tables initialized successfully.")

    def run_build_pipeline(self, df_hist: pd.DataFrame, force_rebuild: bool = True) -> Dict[str, Any]:
        """
        Runs the complete history build pipeline:
        1. Aggregates snapshots.
        2. Scans events.
        3. Scans experiments.
        4. Synthesizes reports and computes vector embeddings.
        """
        if force_rebuild:
            self.rebuild_tables()
            
        df = df_hist.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date").reset_index(drop=True)
        
        # 1. Build Snapshots
        logger.info("Building daily snapshots...")
        unique_dates = sorted(df["date"].unique())
        
        prev_revenues = {}
        snapshots_created = 0
        
        for d_timestamp in unique_dates:
            d_val = pd.to_datetime(d_timestamp).date()
            df_date = df[df["date"] == d_timestamp]
            
            # Build snapshot
            snap = self.snapshot_builder.build_snapshot(df_date, d_val, prev_revenues)
            self.db.add(snap)
            
            # Save product revenues for the next day's growth calculation
            prev_revenues = df_date.groupby("product_id")["revenue"].sum().to_dict()
            snapshots_created += 1
            
        self.db.commit()
        logger.info(f"Daily snapshots saved: {snapshots_created}")
        
        # 2. Build Events
        logger.info("Executing Event Outlier Scan...")
        detected_events = self.event_detector.detect_events(df)
        events_created = 0
        for ev in detected_events:
            self.db.add(ev)
            events_created += 1
            
        self.db.commit()
        logger.info(f"Events saved: {events_created}")
        
        # 3. Build Experiments
        logger.info("Executing Experiment Step-Change Scan...")
        inferred_exps = self.experiment_detector.infer_experiments(df)
        
        # Cap to top 30 most significant experiments by absolute impact and confidence
        inferred_exps = sorted(inferred_exps, key=lambda x: abs(x.improvement_pct) * x.confidence_score, reverse=True)[:30]
        
        experiments_created = 0
        reports_created = 0
        
        logger.info(f"Filtered to top {len(inferred_exps)} most significant experiments. Synthesizing reports...")
        
        for idx, exp in enumerate(inferred_exps):
            self.db.add(exp)
            self.db.commit()  # commit to get exp.id
            
            # 4. Generate report (LLM or Fallback template)
            report = self.report_generator.generate_report(exp)
            report.experiment_id = exp.id
            self.db.add(report)
            self.db.commit()  # commit to get report.id
            
            # 5. Compute embedding and save
            text_to_encode = f"{exp.type} {exp.change_summary} Learnings: {report.structured_json.get('learnings', '')} Recommendations: {report.structured_json.get('recommendations', '')}"
            emb_vector = self.encoder.encode(text_to_encode)
            
            emb = ReportEmbedding(
                report_id=report.id,
                embedding=emb_vector,
                meta_data={
                    "experiment_id": exp.experiment_id,
                    "type": exp.type,
                    "category": exp.category,
                    "outcome": exp.outcome
                }
            )
            self.db.add(emb)
            experiments_created += 1
            reports_created += 1
            
        self.db.commit()
        logger.info(f"Experiments build complete. Inferred: {experiments_created}, Reports/Embeddings: {reports_created}")
        
        return {
            "status": "success",
            "snapshots_created": snapshots_created,
            "events_detected": events_created,
            "experiments_inferred": experiments_created,
            "reports_generated": reports_created
        }

    def semantic_search(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.retriever.semantic_search(query, limit, filters)

    def find_similar_experiments(self, category: str, features: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        return self.retriever.find_similar_experiments(category, features, limit)

    def extract_topic_insights(self, topic: str) -> Dict[str, Any]:
        return self.retriever.extract_topic_insights(topic)

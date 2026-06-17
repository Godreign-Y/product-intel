from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import datetime

from src.core.history.manager import HistoryManager
from src.core.history.storage.models import Snapshot, Event, Experiment, Report
from src.api.dependencies import get_historical_df_from_db
from src.api.schemas.history import (
    SnapshotResponse, EventResponse, ExperimentResponse, ReportResponse,
    SearchRequest, SearchResponse, SearchResponseItem,
    SimilarRequest, SimilarResponse, SimilarResponseItem,
    InsightsResponse
)
# We will define a local dependency helper in dependencies.py, but for now we import get_db
from src.core.history.storage.database import get_db

router = APIRouter(prefix="/history", tags=["Historical Intelligence Repository"])

def get_history_manager(db: Session = Depends(get_db)) -> HistoryManager:
    # Expose a dynamic getter that uses the cached encoder in AppState if initialized
    from src.api.dependencies import AppState
    from src.core.history.embeddings.encoder import SentenceTransformerEncoder
    
    # Preloaded encoder cache from dependencies
    if hasattr(AppState, "history_encoder") and AppState.history_encoder is not None:
        encoder = AppState.history_encoder
    else:
        encoder = SentenceTransformerEncoder()
    return HistoryManager(db, encoder=encoder)

@router.post("/build")
async def build_repository(
    force_rebuild: bool = Query(default=True, description="Wipes database tables and recreates from scratch"),
    manager: HistoryManager = Depends(get_history_manager)
):
    try:
        df_hist = get_historical_df_from_db()
        result = manager.run_build_pipeline(df_hist, force_rebuild=force_rebuild)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@router.get("/snapshots", response_model=List[SnapshotResponse])
async def get_snapshots(
    start_date: Optional[datetime.date] = Query(None),
    end_date: Optional[datetime.date] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Snapshot)
    if start_date:
        query = query.filter(Snapshot.snapshot_date >= start_date)
    if end_date:
        query = query.filter(Snapshot.snapshot_date <= end_date)
    
    results = query.order_by(Snapshot.snapshot_date.desc()).limit(limit).all()
    return results

@router.get("/events", response_model=List[EventResponse])
async def get_events(
    product_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if product_id:
        query = query.filter(Event.product_id == product_id)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)
        
    results = query.order_by(Event.event_date.desc()).limit(limit).all()
    return results

@router.get("/experiments", response_model=List[ExperimentResponse])
async def get_experiments(
    type: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Experiment)
    if type:
        query = query.filter(Experiment.type == type)
    if outcome:
        query = query.filter(Experiment.outcome == outcome)
    if category:
        query = query.filter(Experiment.category == category)
        
    results = query.order_by(Experiment.start_date.desc()).limit(limit).all()
    return results

@router.get("/reports/{experiment_id}", response_model=ReportResponse)
async def get_report_by_experiment(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.experiment_id == experiment_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report for experiment {experiment_id} not found.")
    return report

@router.post("/search", response_model=SearchResponse)
async def semantic_search_endpoint(
    payload: SearchRequest,
    manager: HistoryManager = Depends(get_history_manager)
):
    try:
        search_results = manager.semantic_search(
            query=payload.query,
            limit=payload.limit or 5,
            filters=payload.filters
        )
        
        response_items = []
        for res in search_results:
            rep = res["report"]
            exp = res["experiment"]
            
            response_items.append(
                SearchResponseItem(
                    score=res["score"],
                    experiment=ExperimentResponse.from_orm(exp),
                    report_id=rep.id,
                    structured_json=rep.structured_json,
                    human_readable_text=rep.human_readable_text
                )
            )
            
        return SearchResponse(query=payload.query, results=response_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search query failed: {str(e)}")

@router.post("/similar", response_model=SimilarResponse)
async def find_similar_experiments_endpoint(
    payload: SimilarRequest,
    manager: HistoryManager = Depends(get_history_manager),
    db: Session = Depends(get_db)
):
    try:
        matches = manager.find_similar_experiments(
            category=payload.category,
            features=payload.features,
            limit=payload.limit or 3
        )
        
        response_items = []
        for item in matches:
            exp = item["experiment"]
            # Join the report
            report = db.query(Report).filter(Report.experiment_id == exp.id).first()
            
            response_items.append(
                SimilarResponseItem(
                    similarity_score=item["similarity_score"],
                    experiment=ExperimentResponse.from_orm(exp),
                    report=ReportResponse.from_orm(report) if report else None
                )
            )
            
        return SimilarResponse(matches=response_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity matching failed: {str(e)}")

@router.get("/insights", response_model=InsightsResponse)
async def get_insights_endpoint(
    topic: str = Query(..., description="The query topic to extract recurring insights for, e.g. pricing, checkout"),
    manager: HistoryManager = Depends(get_history_manager)
):
    try:
        insights = manager.extract_topic_insights(topic)
        return InsightsResponse(
            topic=insights["topic"],
            synthesized_rules=insights["synthesized_rules"],
            confidence_score=insights["confidence_score"],
            cached=insights["cached"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge extraction failed: {str(e)}")

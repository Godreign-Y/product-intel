from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.core.decision.manager import DecisionManager
from src.core.history.storage.database import get_db
from src.api.dependencies import AppState, get_historical_data
from src.api.schemas.decision import DecisionRequest, DecisionResponse

router = APIRouter(prefix="/decision", tags=["AI Decision Intelligence Engine"])

def get_decision_manager(db: Session = Depends(get_db)) -> DecisionManager:
    # Build dynamically from preloaded AppState models
    from src.core.history.manager import HistoryManager
    
    df_hist = AppState.df_historical
    forecaster = AppState.forecaster
    sensitivity = AppState.sensitivity_engine
    simulator = AppState.simulator
    
    if df_hist is None or forecaster is None or sensitivity is None or simulator is None:
        # Load state if not preloaded
        from src.api.dependencies import load_app_state
        load_app_state()
        df_hist = AppState.df_historical
        forecaster = AppState.forecaster
        sensitivity = AppState.sensitivity_engine
        simulator = AppState.simulator
        
    history_encoder = AppState.history_encoder
    history_mgr = HistoryManager(db, encoder=history_encoder)
    
    return DecisionManager(
        db=db,
        df_historical=df_hist,
        forecaster=forecaster,
        sensitivity_engine=sensitivity,
        simulator=simulator,
        history_manager=history_mgr,
        explainer=AppState.explainer,
    )

@router.post("/ask", response_model=DecisionResponse)
async def ask_decision_engine(
    payload: DecisionRequest,
    manager: DecisionManager = Depends(get_decision_manager)
):
    try:
        result = manager.process_decision_flow(
            query=payload.query,
            product_id=payload.product_id or "P001",
            session_id=payload.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision Engine loop failed: {str(e)}")

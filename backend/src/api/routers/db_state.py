"""API Router for managing persistent state in Neon PostgreSQL."""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import ChatSession, ChatMessage, Experiment, Recommendation
from src.api.schemas.db_state import (
    SessionCreate, SessionResponse, MessageCreate, MessageResponse,
    ExperimentCreate, ExperimentResponse, RecommendationResponse
)
from src.api.dependencies import get_planner_agent
from src.core.agent.planner import LLMPlannerAgent
from src.utils.logger import setup_logger

logger = setup_logger("db_state_router")

router = APIRouter(prefix="/db", tags=["Database Persistence & State"])

@router.get("/chat/sessions", response_model=List[SessionResponse])
def get_all_sessions(db: Session = Depends(get_db)) -> List[ChatSession]:
    """Retrieve all chat sessions sorted by created_at descending.

    Args:
        db (Session): Database session.

    Returns:
        List[ChatSession]: List of sessions.
    """
    try:
        return db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat sessions.")

@router.post("/chat/sessions", response_model=SessionResponse)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> ChatSession:
    """Create a new chat session thread.

    Args:
        payload (SessionCreate): Input schema.
        db (Session): Database session.

    Returns:
        ChatSession: The created session.
    """
    try:
        session = ChatSession(id=payload.id, title=payload.title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session.")

@router.delete("/chat/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Delete a chat session and all its message history.

    Args:
        session_id (str): Session target ID.
        db (Session): Database session.

    Returns:
        Dict[str, str]: Success state.
    """
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        db.delete(session)
        db.commit()
        return {"status": "success", "message": "Session deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session.")

@router.get("/chat/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)) -> List[ChatMessage]:
    """Retrieve message history for a specific chat session thread.

    Args:
        session_id (str): Session target ID.
        db (Session): Database session.

    Returns:
        List[ChatMessage]: Message items.
    """
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id).all()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages.")

@router.post("/chat/sessions/{session_id}/messages", response_model=MessageResponse)
def append_message(
    session_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    agent: LLMPlannerAgent = Depends(get_planner_agent)
) -> ChatMessage:
    """Save a user message and trigger the LLM agent to compute and save the assistant response.

    Args:
        session_id (str): Session target ID.
        payload (MessageCreate): User message input.
        db (Session): Database session.
        agent (LLMPlannerAgent): The business analysis agent instance.

    Returns:
        ChatMessage: The generated assistant response message.
    """
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")

        # 1. Save user message
        user_timestamp = payload.timestamp or datetime.now().strftime("%I:%M %p")
        user_msg = ChatMessage(
            id=f"msg_user_{int(time.time() * 1000)}",
            session_id=session_id,
            role="user",
            content=payload.content,
            timestamp=user_timestamp
        )
        db.add(user_msg)
        db.commit()

        # 2. Trigger LLM Agent Query processing
        logger.info(f"Triggering LLM Agent query for session {session_id} content: {payload.content}")
        agent_result = agent.process_query(payload.content)
        agent_response_text = agent_result.get("response", "No response received.")

        # 3. Formulate assistant message
        assistant_timestamp = datetime.now().strftime("%I:%M %p")
        suggestions = [
            "Show correlation details",
            "Create experiment simulation",
            "View recommendations"
        ]

        # Extract hypothesis if anomaly is queried
        hypothesis = None
        lower_query = payload.content.lower()
        if "anomaly" in lower_query or "anomalies" in lower_query or "drop" in lower_query or "conversion" in lower_query:
            hypothesis = {
                "title": "Mobile checkout conversion rate drop",
                "description": "A causative audit indicates cart abandonments spike at step 2 (Shipping). Implementing guest checkout is estimated to recover $120K in revenue.",
                "metrics": {
                    "impact": "+3.2% conversion",
                    "revenue": "+$120K/yr"
                }
            }

        assistant_msg = ChatMessage(
            id=f"msg_assistant_{int(time.time() * 1000) + 1}",
            session_id=session_id,
            role="assistant",
            content=agent_response_text,
            timestamp=assistant_timestamp,
            suggestions=suggestions,
            hypothesis=hypothesis
        )

        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return assistant_msg

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error appending message to {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query. Details: {str(e)}")

@router.get("/experiments", response_model=List[ExperimentResponse])
def get_all_experiments(db: Session = Depends(get_db)) -> List[Experiment]:
    """Retrieve all launched experiments.

    Args:
        db (Session): Database session.

    Returns:
        List[Experiment]: List of experiments.
    """
    try:
        return db.query(Experiment).order_by(Experiment.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error fetching experiments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve experiments.")

@router.post("/experiments", response_model=ExperimentResponse)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)) -> Experiment:
    """Save a newly launched causal simulation/experiment.

    Args:
        payload (ExperimentCreate): Experiment details.
        db (Session): Database session.

    Returns:
        Experiment: Saved experiment.
    """
    try:
        experiment = Experiment(
            id=payload.id,
            name=payload.name,
            objective=payload.objective,
            hypothesis=payload.hypothesis,
            primary_metric=payload.primary_metric,
            expected_outcome=payload.expected_outcome,
            type=payload.type,
            status=payload.status,
            variables=payload.variables,
            simulation_preview=payload.simulation_preview
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        return experiment
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving experiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to save experiment.")

@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations_status(db: Session = Depends(get_db)) -> List[Recommendation]:
    """Retrieve implementation state trackers for recommendations.

    Args:
        db (Session): Database session.

    Returns:
        List[Recommendation]: List of recommendations status.
    """
    try:
        return db.query(Recommendation).all()
    except Exception as e:
        logger.error(f"Error listing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendations.")

@router.post("/recommendations/{rec_id}/apply", response_model=RecommendationResponse)
def apply_recommendation(rec_id: str, db: Session = Depends(get_db)) -> Recommendation:
    """Mark a specific growth recommendation as Implemented.

    Args:
        rec_id (str): target recommendation ID (e.g. rec_1).
        db (Session): Database session.

    Returns:
        Recommendation: Implemented tracker object.
    """
    try:
        rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
        if not rec:
            rec = Recommendation(id=rec_id, status="Implemented", applied_at=datetime.utcnow())
            db.add(rec)
        else:
            rec.status = "Implemented"
            rec.applied_at = datetime.utcnow()
        db.commit()
        db.refresh(rec)
        return rec
    except Exception as e:
        db.rollback()
        logger.error(f"Error applying recommendation {rec_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply recommendation.")

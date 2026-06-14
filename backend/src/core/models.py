"""Database models for persistent state storage."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from src.core.database import Base

class ChatSession(Base):
    """Database model for representing conversational agent chat sessions."""
    __tablename__ = "chat_sessions"

    id: str = Column(String(64), primary_key=True, index=True)
    title: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Relationship to messages within the thread
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, id: str, title: str) -> None:
        """Initialize a new chat session.

        Args:
            id (str): Unique thread ID.
            title (str): Display title of session.
        """
        self.id = id
        self.title = title

class ChatMessage(Base):
    """Database model for representing individual messages in an agent chat session."""
    __tablename__ = "chat_messages"

    id: str = Column(String(64), primary_key=True, index=True)
    session_id: str = Column(String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: str = Column(String(20), nullable=False)
    content: str = Column(String, nullable=False)
    timestamp: str = Column(String(32), nullable=False)
    suggestions: Optional[List[str]] = Column(JSON, nullable=True)
    hypothesis: Optional[Dict[str, Any]] = Column(JSON, nullable=True)

    # Bidirectional relationship back to parent session
    session = relationship("ChatSession", back_populates="messages")

    def __init__(
        self,
        id: str,
        session_id: str,
        role: str,
        content: str,
        timestamp: str,
        suggestions: Optional[List[str]] = None,
        hypothesis: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize a new chat message.

        Args:
            id (str): Unique message ID.
            session_id (str): Reference session thread.
            role (str): Sender identity (user/assistant).
            content (str): Text contents.
            timestamp (str): Formatted time string.
            suggestions (Optional[List[str]]): Quick action follow-up prompts.
            hypothesis (Optional[Dict[str, Any]]): Accompanying causal ML hypothesis.
        """
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.suggestions = suggestions
        self.hypothesis = hypothesis

class Experiment(Base):
    """Database model for persisting running/completed causal ML experiments."""
    __tablename__ = "experiments"

    id: str = Column(String(64), primary_key=True, index=True)
    name: str = Column(String(255), nullable=False)
    objective: str = Column(String(255), nullable=False)
    hypothesis: str = Column(String, nullable=False)
    primary_metric: str = Column(String(100), nullable=False)
    expected_outcome: Optional[str] = Column(String(100), nullable=True)
    type: str = Column(String(50), nullable=False)
    status: str = Column(String(30), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    variables: List[Dict[str, Any]] = Column(JSON, nullable=False)
    simulation_preview: Optional[Dict[str, Any]] = Column(JSON, nullable=True)

    def __init__(
        self,
        id: str,
        name: str,
        objective: str,
        hypothesis: str,
        primary_metric: str,
        expected_outcome: Optional[str],
        type: str,
        status: str,
        variables: List[Dict[str, Any]],
        simulation_preview: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize a new experiment instance.

        Args:
            id (str): Experiment unique ID.
            name (str): Display name.
            objective (str): Business target.
            hypothesis (str): Evaluated theory.
            primary_metric (str): Evaluated KPI.
            expected_outcome (Optional[str]): Projected target lift.
            type (str): Experiment methodology.
            status (str): Current execution state.
            variables (List[Dict[str, Any]]): List of altered test factors.
            simulation_preview (Optional[Dict[str, Any]]): Machine learning causality output.
        """
        self.id = id
        self.name = name
        self.objective = objective
        self.hypothesis = hypothesis
        self.primary_metric = primary_metric
        self.expected_outcome = expected_outcome
        self.type = type
        self.status = status
        self.variables = variables
        self.simulation_preview = simulation_preview

class Recommendation(Base):
    """Database model for tracking applied state of optimization suggestions."""
    __tablename__ = "recommendations"

    id: str = Column(String(64), primary_key=True, index=True)
    status: str = Column(String(30), nullable=False)
    applied_at: Optional[datetime] = Column(DateTime, nullable=True)

    def __init__(self, id: str, status: str, applied_at: Optional[datetime] = None) -> None:
        """Initialize a recommendation tracker.

        Args:
            id (str): suggestion ID (e.g. rec_1).
            status (str): current implementation state.
            applied_at (Optional[datetime]): Timestamp of implementation.
        """
        self.id = id
        self.status = status
        self.applied_at = applied_at

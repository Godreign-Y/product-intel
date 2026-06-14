"""Pydantic schemas for database CRUD endpoints."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    """Schema for creating a new chat session."""
    id: str = Field(..., description="Unique ID for the session")
    title: str = Field(..., description="Title of the session")

class MessageResponse(BaseModel):
    """Schema for chat message details."""
    id: str
    session_id: str
    role: str
    content: str
    timestamp: str
    suggestions: Optional[List[str]] = None
    hypothesis: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    """Schema for chat session details."""
    id: str
    title: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    """Schema for inserting a message directly."""
    content: str = Field(..., description="Text content of the message")
    role: Optional[str] = Field(default="user", description="Role of the sender (user/assistant)")
    timestamp: Optional[str] = Field(default=None, description="Formatted time string")
    suggestions: Optional[List[str]] = Field(default=None, description="Actionable suggestion prompts")
    hypothesis: Optional[Dict[str, Any]] = Field(default=None, description="Causal ML hypothesis context")

class ExperimentCreate(BaseModel):
    """Schema for saving a launched experiment."""
    id: str = Field(..., description="Unique experiment ID")
    name: str = Field(..., description="Experiment name")
    objective: str = Field(..., description="Business goal")
    hypothesis: str = Field(..., description="Statement being evaluated")
    primary_metric: str = Field(..., description="Target KPI")
    expected_outcome: Optional[str] = Field(default=None, description="Projected lift")
    type: str = Field(..., description="Methodology (e.g. Simulation)")
    status: str = Field(..., description="Current status")
    variables: List[Dict[str, Any]] = Field(..., description="Altered variables list")
    simulation_preview: Optional[Dict[str, Any]] = Field(default=None, description="Simulation outcome payload")

class ExperimentResponse(BaseModel):
    """Schema for experiment details."""
    id: str
    name: str
    objective: str
    hypothesis: str
    primary_metric: str
    expected_outcome: Optional[str] = None
    type: str
    status: str
    created_at: datetime
    variables: List[Dict[str, Any]]
    simulation_preview: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    """Schema for recommendation implementation details."""
    id: str
    status: str
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True

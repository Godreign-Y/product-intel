from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DecisionRequest(BaseModel):
    query: str = Field(..., example="What might happen if we increase discounts by 10%?")
    product_id: Optional[str] = Field("P001", example="P001")
    session_id: Optional[str] = Field(None, example="session_abc123")

class HypothesisResponseItem(BaseModel):
    hypothesis_id: str
    title: str
    description: str
    generated_from: str
    affected_kpis: List[str]
    confidence_prior: float

class RecommendationResponseItem(BaseModel):
    hypothesis_id: str
    recommendation_text: str
    action_type: str
    expected_kpi_improvement: Dict[str, str]
    estimated_roi: float
    priority: str
    needs_experimentation: bool
    rollback_strategy: str
    confidence_score: float

class DecisionResponse(BaseModel):
    context_id: int
    query: str
    explanation: str
    recommendations: List[RecommendationResponseItem]
    # Allow flexible dict mappings for validation outputs
    ranked_hypotheses: List[Dict[str, Any]]

    class Config:
        from_attributes = True

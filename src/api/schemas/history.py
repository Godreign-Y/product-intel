from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime

# --- Snaphots ---
class SnapshotProductDetail(BaseModel):
    product_id: str
    revenue: float

class SnapshotGrowthDetail(BaseModel):
    product_id: str
    absolute_growth: float
    percentage: float

class SnapshotInventoryAlert(BaseModel):
    product_id: str
    inventory: int

class SnapshotResponse(BaseModel):
    id: int
    snapshot_date: datetime.date
    total_revenue: float
    total_profit: float
    total_orders: int
    mean_conversion_rate: float
    mean_retention_rate: float
    total_marketing_spend: float
    total_inventory: int
    avg_discount_pct: float
    avg_price: float
    
    top_products: Optional[List[SnapshotProductDetail]] = None
    worst_products: Optional[List[SnapshotProductDetail]] = None
    largest_growth: Optional[List[SnapshotGrowthDetail]] = None
    largest_decline: Optional[List[SnapshotGrowthDetail]] = None
    inventory_alerts: Optional[List[SnapshotInventoryAlert]] = None
    channel_mix: Optional[Dict[str, float]] = None
    campaign_mix: Optional[Dict[str, float]] = None
    traffic_mix: Optional[Dict[str, float]] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True

# --- Events ---
class EventResponse(BaseModel):
    id: int
    event_date: datetime.date
    product_id: Optional[str] = None
    event_type: str
    severity: str
    kpis_affected: Optional[str] = None
    reason: Optional[str] = None
    business_impact: Optional[str] = None
    confidence: float

    class Config:
        from_attributes = True

# --- Experiments ---
class ExperimentResponse(BaseModel):
    id: int
    experiment_id: str
    type: str
    product_ids: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    start_date: datetime.date
    end_date: datetime.date
    before_metrics: Optional[Dict[str, float]] = None
    after_metrics: Optional[Dict[str, float]] = None
    change_summary: Optional[str] = None
    improvement_pct: Optional[float] = None
    outcome: str
    confidence_score: float
    
    # Additional fields from experiment_dataset.csv
    subcategory: Optional[str] = None
    changed_features: Optional[Dict[str, Any]] = None
    primary_metric: Optional[str] = None
    expected_direction: Optional[str] = None
    observed_effect_pct: Optional[float] = None
    result: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

# --- Reports ---
class ReportResponse(BaseModel):
    id: int
    experiment_id: int
    structured_json: Optional[Dict[str, Any]] = None
    human_readable_text: Optional[str] = None

    class Config:
        from_attributes = True

# --- Search ---
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResponseItem(BaseModel):
    score: float
    experiment: ExperimentResponse
    report_id: int
    structured_json: Optional[Dict[str, Any]] = None
    human_readable_text: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResponseItem]

# --- Similar ---
class SimilarRequest(BaseModel):
    category: str
    features: Dict[str, Any]
    limit: Optional[int] = 3

class SimilarResponseItem(BaseModel):
    similarity_score: float
    experiment: ExperimentResponse
    report: Optional[ReportResponse] = None

class SimilarResponse(BaseModel):
    matches: List[SimilarResponseItem]

# --- Insights / Knowledge ---
class InsightsResponse(BaseModel):
    topic: str
    synthesized_rules: Dict[str, Any]
    confidence_score: float
    cached: bool

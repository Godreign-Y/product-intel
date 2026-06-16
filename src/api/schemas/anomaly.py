from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class AnomalyRequest(BaseModel):
    product_id: str = Field(..., example="P001")
    target_date: str = Field(..., example="2025-06-15")
    kpi: str = Field("revenue", example="revenue")

class CategoryAnomalyRequest(BaseModel):
    category: str = Field(..., example="Skincare")
    target_date: str = Field(..., example="2025-06-15")
    kpi: str = Field("revenue", example="revenue")

class GlobalAnomalyRequest(BaseModel):
    target_date: str = Field(..., example="2025-06-15")
    kpi: str = Field("revenue", example="revenue")

class AnomalyResponse(BaseModel):
    product_id: str
    target_date: str
    kpi: str
    expected_value: float
    actual_value: float
    residual: float
    percentage_change: float
    severity_score: float
    status: str
    change_point_detected: bool
    change_point_details: Dict[str, Any]
    multivariate_details: Dict[str, Any]
    business_rules_triggered: List[Dict[str, Any]]
    broken_relations: List[Dict[str, Any]]
    business_impact: Dict[str, Any]
    historical_context: Dict[str, Any]
    forecast_monitoring: Dict[str, Any]
    explanation: Dict[str, Any]
    confidence_interval_95: List[float]
    outside_ci: bool
    trend_details: Dict[str, Any]

class CategoryAnomalyResponse(BaseModel):
    category: str
    target_date: str
    kpi: str
    anomalies: List[AnomalyResponse]

class ProductRankingDetail(BaseModel):
    product_id: str
    kpi: str
    severity_score: float
    status: str
    revenue_loss: float
    profit_loss: float
    percent_change: float

class GlobalRankingResponse(BaseModel):
    target_date: str
    kpi: str
    top_10_critical_products: List[ProductRankingDetail]
    top_revenue_risk: List[ProductRankingDetail]
    top_profit_risk: List[ProductRankingDetail]
    most_unusual_products: List[ProductRankingDetail]
    products_recovering: List[ProductRankingDetail]
    products_improving: List[ProductRankingDetail]

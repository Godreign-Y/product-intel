from pydantic import BaseModel, Field
from typing import Dict

class OptimizationRequest(BaseModel):
    target_metric: str = Field("revenue", description="Target metric to maximize, e.g. revenue or profit")
    product_id: str = Field(..., description="Product ID, e.g. PROD_001")
    horizon_days: int = Field(30, ge=1, le=90, description="Inference horizon in days")
    max_discount_pct: float = Field(0.30, ge=0.0, le=0.90, description="Max allowed discount (e.g. 0.30 for 30%)")
    max_marketing_budget: float = Field(250.0, ge=0.0, description="Max daily marketing budget per product")

class OptimalParameters(BaseModel):
    discount_pct: float
    marketing_spend: float
    price: float

class BaselineParameters(BaseModel):
    discount_pct: float
    marketing_spend: float
    price: float

class OptimizationResponse(BaseModel):
    target_metric: str
    product_id: str
    horizon_days: int
    baseline_forecast_sum: float
    optimized_forecast_sum: float
    percentage_improvement: float
    optimal_parameters: OptimalParameters
    baseline_parameters: BaselineParameters

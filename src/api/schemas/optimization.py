from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class OptimizationRequest(BaseModel):
    target_metric: str = Field("revenue", description="Target metric to maximize, e.g. revenue or profit")
    product_id: str = Field(..., description="Product ID, e.g. PROD_001")
    horizon_days: int = Field(30, ge=1, le=90, description="Inference horizon in days")
    max_discount_pct: float = Field(0.30, ge=0.0, le=0.90, description="Max allowed discount (e.g. 0.30 for 30%)")
    max_marketing_budget: float = Field(250.0, ge=0.0, description="Max daily marketing budget per product")
    max_shipping_fee: float = Field(50.0, ge=0.0, description="Max shipping fee to explore")
    n_trials: int = Field(40, ge=10, le=100, description="Number of Bayesian optimization trials")

class OptimalParameters(BaseModel):
    discount_pct: float
    marketing_spend: float
    price: float
    shipping_fee: float = 0.0
    inventory_available: float = 0.0

class BaselineParameters(BaseModel):
    discount_pct: float
    marketing_spend: float
    price: float
    shipping_fee: float = 0.0
    inventory_available: float = 0.0

class KPIImpactItem(BaseModel):
    baseline: float
    optimized: float
    difference: float
    percentage_change: float

class TrialResult(BaseModel):
    trial_number: int
    metric_sum: float
    params: Dict[str, Any]

class OptimizationResponse(BaseModel):
    target_metric: str
    product_id: str
    horizon_days: int
    optimization_method: str = "bayesian_tpe"
    trials_run: int = 40
    baseline_forecast_sum: float
    optimized_forecast_sum: float
    percentage_improvement: float
    optimal_parameters: OptimalParameters
    baseline_parameters: BaselineParameters
    kpi_impact: Optional[Dict[str, KPIImpactItem]] = None
    top_trials: Optional[List[TrialResult]] = None

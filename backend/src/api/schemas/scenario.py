from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModificationDetail(BaseModel):
    type: str = Field(..., description="Type of adjustment: 'add', 'multiply', or 'set'")
    value: float = Field(..., description="The value of the adjustment")

class ScenarioRequest(BaseModel):
    target_metric: str = Field(..., description="Target metric to analyze, e.g. revenue, profit, orders")
    product_id: str = Field(..., description="Product ID, e.g. PROD_001")
    horizon_days: int = Field(30, ge=1, le=90, description="Horizon duration in days")
    modifications: Dict[str, ModificationDetail] = Field(..., description="Modifications dictionary, e.g. {'Discount_Pct': {'type': 'add', 'value': 0.05}}")

class DailyComparisonPoint(BaseModel):
    date: str
    baseline_value: float
    simulated_value: float
    difference: float

class ScenarioResponse(BaseModel):
    target_metric: str
    product_id: str
    horizon_days: int
    modifications: Dict[str, Any]
    baseline_sum: float
    simulated_sum: float
    absolute_difference: float
    percentage_difference: float
    impact: str
    daily_comparison: List[DailyComparisonPoint]

class ScenarioEvaluateRequest(BaseModel):
    product_id: str = Field(..., description="Product ID, e.g. P001")
    horizon_days: int = Field(30, ge=1, le=90, description="Horizon duration in days")
    changes: List[str] = Field(..., description="List of change strings, e.g. ['discount +5%', 'marketing +10%', 'shipping +20']")
    current_features: Optional[Dict[str, float]] = Field(None, description="Optional current state features to override at t=0")

class ScenarioKPISummary(BaseModel):
    baseline: float = Field(..., description="Baseline aggregate value (sum for volumes, mean for rates)")
    simulated: float = Field(..., description="Simulated aggregate value (sum for volumes, mean for rates)")
    absolute_difference: float = Field(..., description="Simulated - Baseline")
    percentage_difference: float = Field(..., description="Percentage change")
    impact: str = Field(..., description="'positive', 'negative', or 'neutral'")

class ScenarioEvaluateResponse(BaseModel):
    product_id: str
    horizon_days: int
    scenario_name: Optional[str] = None
    changes: List[str]
    kpis: Dict[str, ScenarioKPISummary] = Field(..., description="Summary metrics for all 5 target KPIs")
    daily_comparison: Dict[str, List[DailyComparisonPoint]] = Field(..., description="Daily comparison series for each target KPI")

class SingleScenarioConfig(BaseModel):
    scenario_name: str = Field(..., description="Name of the scenario")
    changes: List[str] = Field(..., description="List of changes for this scenario")

class BatchScenarioRequest(BaseModel):
    product_ids: List[str] = Field(..., description="List of product IDs to evaluate")
    horizon_days: int = Field(30, ge=1, le=90, description="Horizon duration in days")
    scenarios: List[SingleScenarioConfig] = Field(..., description="List of scenarios to evaluate")
    current_features: Optional[Dict[str, float]] = Field(None, description="Optional current state features to override at t=0")

class BatchScenarioResponse(BaseModel):
    results: List[ScenarioEvaluateResponse]

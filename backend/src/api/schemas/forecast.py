from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ForecastRequest(BaseModel):
    target_metric: str = Field(..., description="Target metric to forecast. e.g. revenue, profit, orders, conversion_rate, retention_rate")
    product_id: str = Field(..., description="Unique product identifier code, e.g. P001")
    horizon_days: int = Field(30, ge=1, le=90, description="Forecast horizon in days (1 to 90)")
    current_features: Optional[Dict[str, float]] = Field(None, description="Optional: current feature overrides at t=0, e.g. {'marketing_spend': 1000, 'inventory': 200, 'price': 700}")

class ForecastAllRequest(BaseModel):
    product_id: str = Field(..., description="Unique product identifier code, e.g. P001")
    horizon_days: int = Field(30, ge=1, le=90, description="Forecast horizon in days (1 to 90)")
    current_features: Optional[Dict[str, float]] = Field(None, description="Optional: current feature overrides at t=0, e.g. {'marketing_spend': 1000, 'inventory': 200, 'price': 700}")

class DailyForecastPoint(BaseModel):
    date: str
    value: float
    confidence_lower: float
    confidence_upper: float

class ForecastResponse(BaseModel):
    target_metric: str
    product_id: str
    horizon_days: int
    forecast: List[DailyForecastPoint]
    aggregated_sum: float
    aggregated_mean: float

class ForecastAllResponse(BaseModel):
    product_id: str
    horizon_days: int
    revenue: List[DailyForecastPoint]
    profit: List[DailyForecastPoint]
    orders: List[DailyForecastPoint]
    conversion_rate: List[DailyForecastPoint]
    retention_rate: List[DailyForecastPoint]

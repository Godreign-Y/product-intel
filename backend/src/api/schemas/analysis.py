from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ComparisonRequest(BaseModel):
    period1_start: str = Field(..., description="Start of historical Period 1, format YYYY-MM-DD")
    period1_end: str = Field(..., description="End of historical Period 1, format YYYY-MM-DD")
    period2_start: str = Field(..., description="Start of historical Period 2, format YYYY-MM-DD")
    period2_end: str = Field(..., description="End of historical Period 2, format YYYY-MM-DD")
    product_id: Optional[str] = Field(None, description="Optional: specific product ID to analyze")

class MetricComparisonDetail(BaseModel):
    # Depending on target variable, schema has sum or mean fields. We can support optional fields or a generic dictionary
    # For a robust structure, we'll use a dynamic dict or union type in response
    pass

class ComparisonResponse(BaseModel):
    period1_range: str
    period2_range: str
    product_id: Optional[str]
    metrics_comparison: Dict[str, Dict[str, float]]
    drivers_summary: List[str]

class DecliningRequest(BaseModel):
    lookback_days: int = Field(90, ge=7, le=365, description="Lookback window in days to calculate trend")
    metric: str = Field("Revenue", description="Metric to run trend analysis on, e.g. Revenue, Orders")

class DecliningProductDetail(BaseModel):
    product_id: str
    category: str
    slope: float
    total_change: float
    percentage_change: float
    r_squared: float
    p_value: float

class DecliningResponse(BaseModel):
    declining_products: List[DecliningProductDetail]

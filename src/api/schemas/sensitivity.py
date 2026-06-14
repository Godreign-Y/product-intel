from pydantic import BaseModel, Field
from typing import Dict, Optional

class SensitivityRequest(BaseModel):
    product_id: str = Field(..., description="Product ID to analyze, e.g. P001")
    horizon_days: int = Field(default=30, description="Forecast horizon in days")

class SensitivityItem(BaseModel):
    elasticity_score: float = Field(..., description="Percent change in Revenue per 10% change in driver")
    expected_impact: float = Field(..., description="Absolute expected change in cumulative Revenue")
    confidence: str = Field(..., description="Confidence rating: High, Medium, Low")

class SensitivityResponse(BaseModel):
    marketing: SensitivityItem
    discount: SensitivityItem
    shipping: SensitivityItem
    price: SensitivityItem
    inventory: SensitivityItem
    # Mapped 'return' to 'return_rate' or key 'return' for JSON structure matching exactly
    # We will return return_rate in the pydantic schema, but if they want "return" in JSON, we can alias it or use return_rate
    # Let's define the field name as 'return_rate' with alias 'return' so it complies with Python reserved keywords and maps to return in JSON.
    return_rate: SensitivityItem = Field(..., alias="return")

    class Config:
        populate_by_name = True

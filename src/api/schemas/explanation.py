from pydantic import BaseModel, Field
from typing import List, Optional

class ExplanationRequest(BaseModel):
    target_metric: str = Field(..., description="Target metric, e.g. revenue, profit, orders")
    product_id: str = Field(..., description="Product ID, e.g. PROD_001")
    date: str = Field(..., description="Date for which to explain the prediction, format YYYY-MM-DD")

class SHAPContribution(BaseModel):
    feature: str
    clean_name: str
    actual_value: float
    shap_value: float

class GlobalImportanceItem(BaseModel):
    feature: str
    clean_name: str
    importance_value: float

class GlobalImportanceResponse(BaseModel):
    target_metric: str
    global_importance: List[GlobalImportanceItem]

class ExplanationResponse(BaseModel):
    target_metric: str
    product_id: str
    date: str
    prediction_value: float
    base_value: float
    explanation_summary: str
    positive_drivers: List[SHAPContribution]
    negative_drivers: List[SHAPContribution]
    global_importance: List[GlobalImportanceItem]
    shap_contributions: Optional[List[SHAPContribution]] = Field(default=None, description="Deprecated. Use positive/negative drivers instead.")

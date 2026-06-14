from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.api.schemas.explanation import (
    ExplanationRequest, ExplanationResponse, SHAPContribution,
    GlobalImportanceResponse, GlobalImportanceItem
)
from src.api.dependencies import get_explainer, get_historical_data
from src.core.explainer import PredictionExplainer

router = APIRouter(prefix="/explanation", tags=["Explainability"])

@router.post("/explain", response_model=ExplanationResponse)
async def explain_forecast(
    payload: ExplanationRequest,
    explainer: PredictionExplainer = Depends(get_explainer),
    df_hist = Depends(get_historical_data)
):
    try:
        explanation = explainer.explain_prediction(
            historical_df=df_hist,
            product_id=payload.product_id,
            target_metric=payload.target_metric,
            date=payload.date
        )
        
        pos_contribs = [
            SHAPContribution(
                feature=c["feature"],
                clean_name=c["clean_name"],
                actual_value=c["actual_value"],
                shap_value=c["shap_value"]
            )
            for c in explanation["positive_drivers"]
        ]
        
        neg_contribs = [
            SHAPContribution(
                feature=c["feature"],
                clean_name=c["clean_name"],
                actual_value=c["actual_value"],
                shap_value=c["shap_value"]
            )
            for c in explanation["negative_drivers"]
        ]
        
        global_imp = [
            GlobalImportanceItem(
                feature=c["feature"],
                clean_name=c["clean_name"],
                importance_value=c["importance_value"]
            )
            for c in explanation["global_importance"]
        ]
        
        return ExplanationResponse(
            target_metric=explanation["target_metric"],
            product_id=explanation["product_id"],
            date=explanation["date"],
            prediction_value=explanation["prediction_value"],
            base_value=explanation["base_value"],
            explanation_summary=explanation["explanation_summary"],
            positive_drivers=pos_contribs,
            negative_drivers=neg_contribs,
            global_importance=global_imp,
            shap_contributions=pos_contribs + neg_contribs
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal explainability error: {str(e)}")

@router.get("/global_importance", response_model=GlobalImportanceResponse)
async def get_global_importance_endpoint(
    target_metric: str,
    explainer: PredictionExplainer = Depends(get_explainer)
):
    try:
        importance = explainer.get_global_importance(target_metric)
        items = [
            GlobalImportanceItem(
                feature=i["feature"],
                clean_name=i["clean_name"],
                importance_value=i["importance_value"]
            )
            for i in importance
        ]
        return GlobalImportanceResponse(
            target_metric=target_metric,
            global_importance=items
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal global importance error: {str(e)}")

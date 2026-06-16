from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from src.api.schemas.anomaly import (
    AnomalyRequest, CategoryAnomalyRequest, GlobalAnomalyRequest,
    AnomalyResponse, CategoryAnomalyResponse, GlobalRankingResponse
)
from src.api.dependencies import get_anomaly_engine
from src.core.anomaly.engine import AnomalyDetectionEngine

router = APIRouter(prefix="/anomaly", tags=["Anomaly Detection Engine"])

@router.post("/detect", response_model=AnomalyResponse)
async def detect_anomaly_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return res
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection error: {str(e)}")

@router.post("/product", response_model=AnomalyResponse)
async def detect_product_anomaly_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    # Overlaps with detect, provided for compatibility
    return await detect_anomaly_endpoint(payload, engine)

@router.post("/category", response_model=CategoryAnomalyResponse)
async def detect_category_anomalies_endpoint(
    payload: CategoryAnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        anoms = engine.detect_category_anomalies(
            category=payload.category,
            date=payload.target_date,
            kpi=payload.kpi
        )
        return CategoryAnomalyResponse(
            category=payload.category,
            target_date=payload.target_date,
            kpi=payload.kpi,
            anomalies=anoms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Category anomaly detection error: {str(e)}")

@router.post("/history")
async def get_anomaly_history_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {
            "product_id": payload.product_id,
            "target_date": payload.target_date,
            "kpi": payload.kpi,
            "historical_context": res["historical_context"],
            "forecast_monitoring": res["forecast_monitoring"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History context calculation error: {str(e)}")

@router.post("/root-cause")
async def get_anomaly_root_cause_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {
            "product_id": payload.product_id,
            "target_date": payload.target_date,
            "kpi": payload.kpi,
            "root_cause": res["explanation"]["top_drivers"],
            "triggered_rules": res["business_rules_triggered"],
            "broken_relations": res["broken_relations"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Root cause calculation error: {str(e)}")

@router.post("/change-point")
async def get_anomaly_change_point_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {
            "product_id": payload.product_id,
            "target_date": payload.target_date,
            "kpi": payload.kpi,
            "change_point_detected": res["change_point_detected"],
            "change_point_details": res["change_point_details"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change point calculation error: {str(e)}")

@router.post("/business-impact")
async def get_anomaly_business_impact_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {
            "product_id": payload.product_id,
            "target_date": payload.target_date,
            "kpi": payload.kpi,
            "business_impact": res["business_impact"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business impact calculation error: {str(e)}")

@router.post("/top-products", response_model=GlobalRankingResponse)
async def get_top_products_endpoint(
    payload: GlobalAnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.get_top_products(
            date=payload.target_date,
            kpi=payload.kpi
        )
        return GlobalRankingResponse(
            target_date=payload.target_date,
            kpi=payload.kpi,
            top_10_critical_products=res["top_10_critical_products"],
            top_revenue_risk=res["top_revenue_risk"],
            top_profit_risk=res["top_profit_risk"],
            most_unusual_products=res["most_unusual_products"],
            products_recovering=res["products_recovering"],
            products_improving=res["products_improving"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Global ranking ranking error: {str(e)}")

@router.post("/explain")
async def get_anomaly_explain_endpoint(
    payload: AnomalyRequest,
    engine: AnomalyDetectionEngine = Depends(get_anomaly_engine)
):
    try:
        res = engine.run_detection(
            product_id=payload.product_id,
            target_date=payload.target_date,
            kpi=payload.kpi
        )
        if "error" in res:
            raise HTTPException(status_code=400, detail=res["error"])
        return {
            "product_id": payload.product_id,
            "target_date": payload.target_date,
            "kpi": payload.kpi,
            "explanation": res["explanation"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly explanation error: {str(e)}")

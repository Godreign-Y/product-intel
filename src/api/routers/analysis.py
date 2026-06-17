from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.analysis import ComparisonRequest, ComparisonResponse, DecliningRequest, DecliningResponse, DecliningProductDetail
from src.api.dependencies import get_analyzer, get_historical_df_from_db, get_max_date_from_db
from src.core.analyzer import BusinessAnalyzer
import pandas as pd

router = APIRouter(prefix="/analysis", tags=["Business Analysis"])

@router.post("/compare", response_model=ComparisonResponse)
async def compare_periods(
    payload: ComparisonRequest,
    analyzer: BusinessAnalyzer = Depends(get_analyzer)
):
    try:
        p1_start = pd.to_datetime(payload.period1_start)
        p1_end = pd.to_datetime(payload.period1_end)
        p2_start = pd.to_datetime(payload.period2_start)
        p2_end = pd.to_datetime(payload.period2_end)
        
        start_date = min(p1_start, p2_start)
        end_date = max(p1_end, p2_end)
        
        df_hist = get_historical_df_from_db(
            start_date=start_date,
            end_date=end_date,
            product_id=payload.product_id
        )
        
        result = analyzer.compare_periods(
            df=df_hist,
            period1_start=payload.period1_start,
            period1_end=payload.period1_end,
            period2_start=payload.period2_start,
            period2_end=payload.period2_end,
            product_id=payload.product_id
        )
        
        return ComparisonResponse(
            period1_range=result["period1_range"],
            period2_range=result["period2_range"],
            product_id=result["product_id"],
            metrics_comparison=result["metrics_comparison"],
            drivers_summary=result["drivers_summary"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal comparison error: {str(e)}")

@router.post("/declining", response_model=DecliningResponse)
async def list_declining_products(
    payload: DecliningRequest,
    analyzer: BusinessAnalyzer = Depends(get_analyzer)
):
    try:
        max_date = get_max_date_from_db()
        cutoff_date = max_date - pd.Timedelta(days=payload.lookback_days)
        df_hist = get_historical_df_from_db(start_date=cutoff_date)
        
        declined_list = analyzer.detect_declining_products(
            df=df_hist,
            lookback_days=payload.lookback_days,
            metric=payload.metric
        )
        
        products = [
            DecliningProductDetail(
                product_id=item["product_id"],
                category=item["category"],
                slope=item["slope"],
                total_change=item["total_change"],
                percentage_change=item["percentage_change"],
                r_squared=item["r_squared"],
                p_value=item["p_value"]
            )
            for item in declined_list
        ]
        
        return DecliningResponse(declining_products=products)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal trend analysis error: {str(e)}")

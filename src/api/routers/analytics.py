from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.analytics import (
    AnalyticsRequest, TrendRequest, ProductAnalyticsRequest,
    KPISummaryResponse, TrendResponse, BenchmarkResponse,
    SeasonalityResponse, ChannelResponse, CampaignResponse,
    InventoryResponse, CustomerResponse, MarketingResponse,
    PricingResponse
)
from src.api.dependencies import get_analytics_engine
from src.core.analytics import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["Analytics Engine"])

@router.post("/kpi", response_model=KPISummaryResponse)
async def get_kpis_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_kpis(
            start_date=payload.start_date,
            end_date=payload.end_date,
            product_id=payload.product_id,
            category=payload.category
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI Summary calculation error: {str(e)}")

@router.post("/trend", response_model=TrendResponse)
async def get_trends_endpoint(
    payload: TrendRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_trends(
            metric=payload.metric,
            start_date=payload.start_date,
            end_date=payload.end_date,
            product_id=payload.product_id,
            granularity=payload.granularity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend calculation error: {str(e)}")

@router.post("/benchmark", response_model=BenchmarkResponse)
async def get_benchmarks_endpoint(
    payload: ProductAnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_benchmarks(
            product_id=payload.product_id,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark calculation error: {str(e)}")

@router.post("/seasonality", response_model=SeasonalityResponse)
async def get_seasonality_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_seasonality(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seasonality calculation error: {str(e)}")

@router.post("/channel", response_model=ChannelResponse)
async def get_channels_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_channels(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Channel calculation error: {str(e)}")

@router.post("/campaign", response_model=CampaignResponse)
async def get_campaigns_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_campaigns(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign calculation error: {str(e)}")

@router.post("/inventory", response_model=InventoryResponse)
async def get_inventory_endpoint(
    payload: ProductAnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_inventory(
            product_id=payload.product_id,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory calculation error: {str(e)}")

@router.post("/customer", response_model=CustomerResponse)
async def get_customers_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_customers(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer calculation error: {str(e)}")

@router.post("/marketing", response_model=MarketingResponse)
async def get_marketing_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_marketing(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Marketing calculation error: {str(e)}")

@router.post("/pricing", response_model=PricingResponse)
async def get_pricing_endpoint(
    payload: AnalyticsRequest,
    engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    try:
        return engine.get_pricing(
            product_id=payload.product_id,
            category=payload.category,
            start_date=payload.start_date,
            end_date=payload.end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing calculation error: {str(e)}")

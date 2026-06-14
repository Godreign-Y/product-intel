from fastapi import APIRouter, Depends, HTTPException
import numpy as np
from typing import List

from src.api.schemas.forecast import ForecastRequest, ForecastResponse, DailyForecastPoint, ForecastAllRequest, ForecastAllResponse
from src.api.dependencies import get_forecaster, get_historical_data
from src.core.forecaster import ProductForecaster

router = APIRouter(prefix="/forecast", tags=["Forecasting"])

@router.post("/predict", response_model=ForecastResponse)
async def predict_forecast(
    payload: ForecastRequest,
    forecaster: ProductForecaster = Depends(get_forecaster),
    df_hist = Depends(get_historical_data)
):
    try:
        # Run recursive multi-step forecasting with optional current_features warm-start
        forecast_df = forecaster.forecast(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            future_overrides=None,
            current_features=payload.current_features
        )
        
        target_lower = payload.target_metric.lower()
        if target_lower not in forecast_df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Target metric {payload.target_metric} not found in model targets."
            )
            
        values = forecast_df[target_lower].values
        lowers = forecast_df[f"{target_lower}_conf_lower"].values
        uppers = forecast_df[f"{target_lower}_conf_upper"].values
        dates = forecast_df["date"].dt.strftime("%Y-%m-%d").values
        
        forecast_points = [
            DailyForecastPoint(
                date=d, 
                value=float(v),
                confidence_lower=float(l),
                confidence_upper=float(u)
            )
            for d, v, l, u in zip(dates, values, lowers, uppers)
        ]
        
        agg_sum = float(np.sum(values))
        agg_mean = float(np.mean(values))
        
        return ForecastResponse(
            target_metric=payload.target_metric,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            forecast=forecast_points,
            aggregated_sum=round(agg_sum, 2),
            aggregated_mean=round(agg_mean, 4)
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal forecast error: {str(e)}")

@router.post("/predict_all", response_model=ForecastAllResponse)
async def predict_all_forecasts(
    payload: ForecastAllRequest,
    forecaster: ProductForecaster = Depends(get_forecaster),
    df_hist = Depends(get_historical_data)
):
    try:
        # Run recursive multi-step forecasting for all metrics
        forecast_df = forecaster.forecast(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            future_overrides=None,
            current_features=payload.current_features
        )
        
        dates = forecast_df["date"].dt.strftime("%Y-%m-%d").values
        targets = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
        
        results = {}
        for target in targets:
            values = forecast_df[target].values
            lowers = forecast_df[f"{target}_conf_lower"].values
            uppers = forecast_df[f"{target}_conf_upper"].values
            
            points = [
                DailyForecastPoint(
                    date=d, 
                    value=float(v),
                    confidence_lower=float(l),
                    confidence_upper=float(u)
                )
                for d, v, l, u in zip(dates, values, lowers, uppers)
            ]
            results[target] = points
            
        return ForecastAllResponse(
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            revenue=results["revenue"],
            profit=results["profit"],
            orders=results["orders"],
            conversion_rate=results["conversion_rate"],
            retention_rate=results["retention_rate"]
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal forecast error: {str(e)}")

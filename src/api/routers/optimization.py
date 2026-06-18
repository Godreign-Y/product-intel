from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.optimization import (
    OptimizationRequest, OptimizationResponse,
    OptimalParameters, BaselineParameters, KPIImpactItem, TrialResult
)
from src.api.dependencies import get_optimizer, get_historical_df_from_db
from src.core.optimizer import RevenueOptimizer

router = APIRouter(prefix="/optimization", tags=["Optimization"])

@router.post("/maximize", response_model=OptimizationResponse)
async def maximize_metric(
    payload: OptimizationRequest,
    optimizer: RevenueOptimizer = Depends(get_optimizer)
):
    try:
        df_hist = get_historical_df_from_db(product_id=payload.product_id)
        print("\n[ROUTER DEBUG] df_hist shape:", df_hist.shape)
        print("[ROUTER DEBUG] df_hist columns:", list(df_hist.columns))
        print("[ROUTER DEBUG] df_hist nulls:\n", df_hist.isnull().sum()[df_hist.isnull().sum() > 0])
        result = optimizer.optimize_parameters(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            target_metric=payload.target_metric,
            max_discount_pct=payload.max_discount_pct,
            max_marketing_budget=payload.max_marketing_budget,
            max_shipping_fee=payload.max_shipping_fee,
            n_trials=payload.n_trials,
        )
        
        opt_params = OptimalParameters(
            discount_pct=result["optimal_parameters"]["discount_pct"],
            marketing_spend=result["optimal_parameters"]["marketing_spend"],
            price=result["optimal_parameters"]["price"],
            shipping_fee=result["optimal_parameters"].get("shipping_fee", 0.0),
            inventory_available=result["optimal_parameters"].get("inventory_available", 0.0),
        )
        
        base_params = BaselineParameters(
            discount_pct=result["baseline_parameters"]["discount_pct"],
            marketing_spend=result["baseline_parameters"]["marketing_spend"],
            price=result["baseline_parameters"]["price"],
            shipping_fee=result["baseline_parameters"].get("shipping_fee", 0.0),
            inventory_available=result["baseline_parameters"].get("inventory_available", 0.0),
        )
        
        # Map KPI impact
        kpi_impact = None
        if "kpi_impact" in result:
            kpi_impact = {
                k: KPIImpactItem(**v)
                for k, v in result["kpi_impact"].items()
            }
        
        # Map top trials
        top_trials = None
        if "top_trials" in result:
            top_trials = [TrialResult(**t) for t in result["top_trials"]]
        
        return OptimizationResponse(
            target_metric=result["target_metric"],
            product_id=result["product_id"],
            horizon_days=result["horizon_days"],
            optimization_method=result.get("optimization_method", "bayesian_tpe"),
            trials_run=result.get("trials_run", 40),
            baseline_forecast_sum=result["baseline_forecast_sum"],
            optimized_forecast_sum=result["optimized_forecast_sum"],
            percentage_improvement=result["percentage_improvement"],
            optimal_parameters=opt_params,
            baseline_parameters=base_params,
            kpi_impact=kpi_impact,
            top_trials=top_trials,
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal optimization error: {str(e)}")

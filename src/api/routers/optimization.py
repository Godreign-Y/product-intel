from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.optimization import OptimizationRequest, OptimizationResponse, OptimalParameters, BaselineParameters
from src.api.dependencies import get_optimizer, get_historical_data
from src.core.optimizer import RevenueOptimizer

router = APIRouter(prefix="/optimization", tags=["Optimization"])

@router.post("/maximize", response_model=OptimizationResponse)
async def maximize_metric(
    payload: OptimizationRequest,
    optimizer: RevenueOptimizer = Depends(get_optimizer),
    df_hist = Depends(get_historical_data)
):
    try:
        result = optimizer.optimize_parameters(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            target_metric=payload.target_metric,
            max_discount_pct=payload.max_discount_pct,
            max_marketing_budget=payload.max_marketing_budget
        )
        
        opt_params = OptimalParameters(
            discount_pct=result["optimal_parameters"]["discount_pct"],
            marketing_spend=result["optimal_parameters"]["marketing_spend"],
            price=result["optimal_parameters"]["price"]
        )
        
        base_params = BaselineParameters(
            discount_pct=result["baseline_parameters"]["discount_pct"],
            marketing_spend=result["baseline_parameters"]["marketing_spend"],
            price=result["baseline_parameters"]["price"]
        )
        
        return OptimizationResponse(
            target_metric=result["target_metric"],
            product_id=result["product_id"],
            horizon_days=result["horizon_days"],
            baseline_forecast_sum=result["baseline_forecast_sum"],
            optimized_forecast_sum=result["optimized_forecast_sum"],
            percentage_improvement=result["percentage_improvement"],
            optimal_parameters=opt_params,
            baseline_parameters=base_params
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal optimization error: {str(e)}")

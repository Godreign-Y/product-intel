from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from src.api.schemas.scenario import (
    ScenarioRequest, ScenarioResponse, DailyComparisonPoint,
    ScenarioEvaluateRequest, ScenarioEvaluateResponse, ScenarioKPISummary,
    BatchScenarioRequest, BatchScenarioResponse
)
from src.api.dependencies import get_simulator, get_historical_df_from_db
from src.core.simulator import ScenarioSimulator

router = APIRouter(prefix="/scenario", tags=["Scenario Analysis"])

@router.post("/simulate", response_model=ScenarioResponse)
async def simulate_what_if(
    payload: ScenarioRequest,
    simulator: ScenarioSimulator = Depends(get_simulator)
):
    try:
        df_hist = get_historical_df_from_db(product_id=payload.product_id)
        # Convert modifications payload to simple dict structure
        mods = {
            k: {"type": v.type, "value": v.value}
            for k, v in payload.modifications.items()
        }
        
        # Run simulation
        result = simulator.simulate_what_if(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            target_metric=payload.target_metric,
            modifications=mods
        )
        
        comparison_points = [
            DailyComparisonPoint(
                date=p["date"],
                baseline_value=p["baseline_value"],
                simulated_value=p["simulated_value"],
                difference=p["difference"]
            )
            for p in result["daily_comparison"]
        ]
        
        return ScenarioResponse(
            target_metric=result["target_metric"],
            product_id=result["product_id"],
            horizon_days=result["horizon_days"],
            modifications=result["modifications"],
            baseline_sum=result["baseline_sum"],
            simulated_sum=result["simulated_sum"],
            absolute_difference=result["absolute_difference"],
            percentage_difference=result["percentage_difference"],
            impact=result["impact"],
            daily_comparison=comparison_points
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal simulation error: {str(e)}")

@router.post("/evaluate", response_model=ScenarioEvaluateResponse)
async def evaluate_scenario(
    payload: ScenarioEvaluateRequest,
    simulator: ScenarioSimulator = Depends(get_simulator)
):
    try:
        df_hist = get_historical_df_from_db(product_id=payload.product_id)
        result = simulator.evaluate_scenario(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days,
            changes=payload.changes,
            current_features=payload.current_features
        )
        
        kpis_response = {}
        for target, kpi in result["kpis"].items():
            kpis_response[target] = ScenarioKPISummary(
                baseline=kpi["baseline"],
                simulated=kpi["simulated"],
                absolute_difference=kpi["absolute_difference"],
                percentage_difference=kpi["percentage_difference"],
                impact=kpi["impact"]
            )
            
        daily_response = {}
        for target, series in result["daily_comparison"].items():
            daily_response[target] = [
                DailyComparisonPoint(
                    date=p["date"],
                    baseline_value=p["baseline_value"],
                    simulated_value=p["simulated_value"],
                    difference=p["difference"]
                )
                for p in series
            ]
            
        return ScenarioEvaluateResponse(
            product_id=result["product_id"],
            horizon_days=result["horizon_days"],
            changes=result["changes"],
            kpis=kpis_response,
            daily_comparison=daily_response
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal scenario evaluation error: {str(e)}")

@router.post("/evaluate_batch", response_model=BatchScenarioResponse)
async def evaluate_batch_scenarios(
    payload: BatchScenarioRequest,
    simulator: ScenarioSimulator = Depends(get_simulator)
):
    try:
        results = []
        for product_id in payload.product_ids:
            df_hist = get_historical_df_from_db(product_id=product_id)
            for scenario_conf in payload.scenarios:
                result = simulator.evaluate_scenario(
                    historical_df=df_hist,
                    product_id=product_id,
                    horizon_days=payload.horizon_days,
                    changes=scenario_conf.changes,
                    current_features=payload.current_features
                )
                
                kpis_response = {}
                for target, kpi in result["kpis"].items():
                    kpis_response[target] = ScenarioKPISummary(
                        baseline=kpi["baseline"],
                        simulated=kpi["simulated"],
                        absolute_difference=kpi["absolute_difference"],
                        percentage_difference=kpi["percentage_difference"],
                        impact=kpi["impact"]
                    )
                    
                daily_response = {}
                for target, series in result["daily_comparison"].items():
                    daily_response[target] = [
                        DailyComparisonPoint(
                            date=p["date"],
                            baseline_value=p["baseline_value"],
                            simulated_value=p["simulated_value"],
                            difference=p["difference"]
                        )
                        for p in series
                    ]
                
                results.append(
                    ScenarioEvaluateResponse(
                        product_id=result["product_id"],
                        horizon_days=result["horizon_days"],
                        scenario_name=scenario_conf.scenario_name,
                        changes=result["changes"],
                        kpis=kpis_response,
                        daily_comparison=daily_response
                    )
                )
                
        return BatchScenarioResponse(results=results)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal batch scenario evaluation error: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.sensitivity import SensitivityRequest, SensitivityResponse, SensitivityItem
from src.api.dependencies import get_sensitivity_engine, get_historical_data
from src.core.sensitivity import SensitivityEngine

router = APIRouter(prefix="/sensitivity", tags=["Sensitivity Engine"])

@router.post("/estimate", response_model=SensitivityResponse)
async def estimate_sensitivity_endpoint(
    payload: SensitivityRequest,
    engine: SensitivityEngine = Depends(get_sensitivity_engine),
    df_hist = Depends(get_historical_data)
):
    try:
        results = engine.calculate_sensitivity(
            historical_df=df_hist,
            product_id=payload.product_id,
            horizon_days=payload.horizon_days
        )
        
        # Structure the response
        return SensitivityResponse(
            marketing=SensitivityItem(
                elasticity_score=results["marketing"]["elasticity_score"],
                expected_impact=results["marketing"]["expected_impact"],
                confidence=results["marketing"]["confidence"]
            ),
            discount=SensitivityItem(
                elasticity_score=results["discount"]["elasticity_score"],
                expected_impact=results["discount"]["expected_impact"],
                confidence=results["discount"]["confidence"]
            ),
            shipping=SensitivityItem(
                elasticity_score=results["shipping"]["elasticity_score"],
                expected_impact=results["shipping"]["expected_impact"],
                confidence=results["shipping"]["confidence"]
            ),
            price=SensitivityItem(
                elasticity_score=results["price"]["elasticity_score"],
                expected_impact=results["price"]["expected_impact"],
                confidence=results["price"]["confidence"]
            ),
            inventory=SensitivityItem(
                elasticity_score=results["inventory"]["elasticity_score"],
                expected_impact=results["inventory"]["expected_impact"],
                confidence=results["inventory"]["confidence"]
            ),
            return_rate=SensitivityItem(
                elasticity_score=results["return"]["elasticity_score"],
                expected_impact=results["return"]["expected_impact"],
                confidence=results["return"]["confidence"]
            )
        )
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal sensitivity estimation error: {str(e)}")

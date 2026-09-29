from fastapi import APIRouter, HTTPException, status

from app.core.science.consumables import calculate_eva_consumables
from app.schemas.mission import ConsumablesRequest, ConsumablesResponse

router = APIRouter(prefix="/api/v1/mission", tags=["Mission Planning"])


@router.post(
    "/consumables",
    response_model=ConsumablesResponse,
    status_code=status.HTTP_200_OK,
)
def estimate_mission_consumables(request: ConsumablesRequest):
    """Calculates estimated duration, oxygen usage, and safety margins for an EVA mission

    given route distance, terrain roughness, slope, and payload weight.
    """
    try:
        return calculate_eva_consumables(request)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while calculating mission consumables.",
        )

"""Endpoint for option premium estimation at target underlying spot."""

from fastapi import APIRouter, status

from app.schemas.requests import EstimateRequest
from app.schemas.responses import EstimateResponse
from app.services.option_estimation import estimate_option_target


router = APIRouter()


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate Option Premium at Target Spot",
    description=(
        "Estimates the theoretical premium of a selected NIFTY option when the underlying "
        "reaches a user-defined target spot price.\n\n"
        "Calculates:\n"
        "- Base estimated premium at the target underlying spot\n"
        "- Target arrival time and remaining time to expiry (ACT/365)\n"
        "- Conservative, base, and optimistic IV scenarios (absolute percentage point shifts)\n"
        "- Black-Scholes-Merton Greeks at target conditions\n"
        "- Projected gross profit/loss and gross ROI percentage\n"
        "- Flat-underlying time-decay comparison\n\n"
        "All calculations assume continuous dividend yield and European exercise."
    ),
    responses={
        200: {"description": "Option estimation calculated successfully."},
        400: {"description": "Invalid financial parameters or mathematical boundary error."},
        422: {"description": "Validation error: invalid request payload or missing fields."},
    },
)
async def estimate_option(request: EstimateRequest) -> EstimateResponse:
    """Estimate option premium, scenarios, Greeks, and P&L at target spot."""
    return estimate_option_target(request)

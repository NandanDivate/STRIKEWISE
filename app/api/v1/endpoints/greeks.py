"""Endpoint for calculating option Greeks."""

from fastapi import APIRouter, status

from app.schemas.requests import GreeksRequest
from app.schemas.responses import GreeksResponse
from app.services.option_estimation import calculate_greeks_service


router = APIRouter()


@router.post(
    "/greeks",
    response_model=GreeksResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Option Greeks",
    description=(
        "Calculates Black-Scholes-Merton Greeks (Delta, Gamma, Theta, Vega, Rho) "
        "for a supplied European option contract and market conditions.\n\n"
        "Units:\n"
        "- `delta`: Premium change per 1-point move in underlying index\n"
        "- `gamma`: Change in Delta per 1-point move in underlying index\n"
        "- `theta`: Premium change per calendar day (annual derivative / 365)\n"
        "- `vega`: Premium change for a 1 percentage point move in IV\n"
        "- `rho`: Premium change for a 1 percentage point move in interest rate"
    ),
    responses={
        200: {"description": "Greeks calculated successfully."},
        400: {"description": "Invalid input parameters."},
        422: {"description": "Validation error: invalid request payload."},
    },
)
async def greeks_endpoint(request: GreeksRequest) -> GreeksResponse:
    """Calculate option Greeks for a supplied contract and market parameters."""
    return calculate_greeks_service(request)

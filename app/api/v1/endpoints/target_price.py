"""Endpoint for calculating required exit premium to achieve a gross profit goal."""

from fastapi import APIRouter, status

from app.schemas.requests import TargetPriceRequest
from app.schemas.responses import TargetPriceResponse
from app.services.option_estimation import calculate_target_exit_price


router = APIRouter()


@router.post(
    "/target-price",
    response_model=TargetPriceResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Required Exit Premium for Profit Target",
    description=(
        "Calculates the option exit premium required to achieve a user-defined gross "
        "profit percentage from an entry premium.\n\n"
        "Formula:\n"
        "- `required_exit_premium = entry_premium * (1 + target_profit_percent / 100)`\n"
        "- `gross_profit_per_unit = required_exit_premium - entry_premium`\n"
        "- `gross_pnl = gross_profit_per_unit * quantity` (if quantity is supplied)\n\n"
        "Note: This is a premium target calculation, not a forecast of the underlying spot."
    ),
    responses={
        200: {"description": "Target exit premium calculated successfully."},
        422: {"description": "Validation error: invalid request payload."},
    },
)
async def target_price_endpoint(request: TargetPriceRequest) -> TargetPriceResponse:
    """Calculate the required exit premium for a specified profit target."""
    return calculate_target_exit_price(request)

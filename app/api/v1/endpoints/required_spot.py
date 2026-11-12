"""Endpoint for reverse-solving the required underlying spot to reach a target premium."""

from fastapi import APIRouter, status

from app.schemas.requests import RequiredSpotRequest
from app.schemas.responses import RequiredSpotResponse
from app.services.option_estimation import calculate_required_spot_service


router = APIRouter()


@router.post(
    "/required-spot",
    response_model=RequiredSpotResponse,
    status_code=status.HTTP_200_OK,
    summary="Reverse-Solve Required Underlying Spot",
    description=(
        "Reverse-solves the underlying spot required for an option to reach a specified "
        "target premium using SciPy Brent's root-finding method.\n\n"
        "Features:\n"
        "- Safe dynamic bracketing\n"
        "- Detects mathematically unattainable targets (e.g. Put target >= K * exp(-rT))\n"
        "- Verifies repricing error of the root\n"
        "- Returns explicit solver status (`solution_found`, `unattainable_target`, or `no_solution_in_search_range`)"
    ),
    responses={
        200: {"description": "Solver executed successfully."},
        400: {"description": "Invalid input parameters."},
        422: {"description": "Validation error: invalid request payload."},
    },
)
async def required_spot_endpoint(request: RequiredSpotRequest) -> RequiredSpotResponse:
    """Reverse-solve the underlying spot required to reach a target option premium."""
    return calculate_required_spot_service(request)

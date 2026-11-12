"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.responses import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service status, version, and current timestamp. Does not require any credentials.",
)
async def health_check() -> HealthResponse:
    """Return the current health status of the API."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        service="NIFTY Options Pricing API",
        timestamp=datetime.now(timezone.utc),
    )


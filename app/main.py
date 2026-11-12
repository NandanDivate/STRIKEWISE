"""NIFTY Options Pricing API — FastAPI application entry point.

A quantitative options pricing service that estimates theoretical premiums
for NIFTY options using the Black-Scholes-Merton model.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="NIFTY Options Pricing API",
    description=(
        "A quantitative options pricing service that estimates theoretical premiums "
        "for NIFTY CE/PE options using the Black-Scholes-Merton model. "
        "Supports manual market-data input, IV scenario analysis, Greeks calculation, "
        "reverse spot solving, and gross P&L estimation. "
        "All estimates are theoretical and do not constitute financial advice."
    ),
    version="0.1.0",
)

# CORS middleware — restricted origins from settings, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include API v1 router
app.include_router(v1_router, prefix="/api/v1")


@app.get(
    "/health",
    summary="Root Health Check",
    description="Returns service status and version at the root level.",
    tags=["Health"],
)
async def root_health() -> dict:
    """Root-level health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "NIFTY Options Pricing API",
    }


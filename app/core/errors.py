"""Custom exception classes and FastAPI exception handlers.

Provides a consistent error response schema across the API.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Error response schema
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Consistent error response returned by the API."""

    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when request data fails domain-level validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class PricingError(Exception):
    """Raised when the pricing engine encounters an error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class SolverError(Exception):
    """Raised when the numerical solver fails to converge or find a root."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class MarketDataError(Exception):
    """Raised when market data retrieval fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application."""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="VALIDATION_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(PricingError)
    async def pricing_error_handler(
        request: Request, exc: PricingError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="PRICING_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(SolverError)
    async def solver_error_handler(
        request: Request, exc: SolverError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="SOLVER_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(MarketDataError)
    async def market_data_error_handler(
        request: Request, exc: MarketDataError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                error_code="MARKET_DATA_ERROR",
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected internal error occurred.",
                details=None,
            ).model_dump(),
        )


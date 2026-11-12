"""Pydantic v2 request schemas for the NIFTY Options Pricing API.

All percentage inputs (IV, risk-free rate, dividend yield) are in percentage
form in the API (e.g., 15.0 means 15%) and converted to decimals internally
by the pricing engine.

Expiry must always be a timezone-aware datetime. Naive datetimes are rejected.
"""

import math
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

OptionType = Literal["CE", "PE"]


class EstimateRequest(BaseModel):
    """Request schema for the /options/estimate endpoint.

    Estimates the theoretical premium of a selected NIFTY option
    when the underlying reaches a user-defined target spot price.
    """

    underlying_symbol: str = Field(
        default="NIFTY",
        description="Underlying index symbol.",
    )
    current_spot: float = Field(
        ...,
        gt=0,
        description="Current underlying spot price in index points.",
    )
    target_spot: float = Field(
        ...,
        gt=0,
        description="Target underlying spot price in index points.",
    )
    option_type: OptionType = Field(
        ...,
        description="Option type: 'CE' for Call, 'PE' for Put.",
    )
    strike_price: float = Field(
        ...,
        gt=0,
        description="Strike price of the option in index points.",
    )
    entry_premium: float = Field(
        ...,
        gt=0,
        description="Entry premium paid per unit for the option.",
    )
    quantity: int = Field(
        default=1,
        gt=0,
        description="Number of option units (not lots).",
    )
    expiry: datetime = Field(
        ...,
        description="Expiry date and time as a timezone-aware ISO 8601 timestamp.",
    )
    expected_time_to_target_minutes: float = Field(
        ...,
        gt=0,
        description="Expected time for the underlying to reach the target spot, in minutes.",
    )
    implied_volatility_percent: float = Field(
        ...,
        ge=0.01,
        le=500.0,
        description="Annualized implied volatility in percentage (e.g., 15.0 means 15%).",
    )
    risk_free_rate_percent: float = Field(
        default=7.0,
        ge=0.0,
        le=100.0,
        description="Annual risk-free interest rate in percentage (default 7.0%).",
    )
    dividend_yield_percent: float = Field(
        default=1.2,
        ge=0.0,
        le=50.0,
        description="Annual continuous dividend yield in percentage (default 1.2%).",
    )
    iv_shift_points: Optional[float] = Field(
        default=2.0,
        description="IV shift in percentage points for scenario generation (default 2.0).",
    )

    @field_validator("expiry")
    @classmethod
    def expiry_must_be_timezone_aware(cls, v: datetime) -> datetime:
        """Reject naive (timezone-unaware) expiry timestamps."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Expiry must be a timezone-aware datetime (include timezone offset).")
        return v

    @field_validator(
        "current_spot",
        "target_spot",
        "strike_price",
        "entry_premium",
        "implied_volatility_percent",
        "risk_free_rate_percent",
        "dividend_yield_percent",
        "expected_time_to_target_minutes",
    )
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        """Reject non-finite numeric values (inf, -inf, NaN)."""
        if not math.isfinite(v):
            raise ValueError("Value must be a finite number.")
        return v


class TargetPriceRequest(BaseModel):
    """Request schema for the /options/target-price endpoint.

    Calculates the exit premium needed to achieve a user-defined
    gross profit percentage from entry premium.
    """

    entry_premium: float = Field(
        ...,
        gt=0,
        description="Entry premium paid per unit for the option.",
    )
    target_profit_percent: float = Field(
        ...,
        gt=0,
        description="Desired gross profit percentage (e.g., 50.0 means 50% profit).",
    )
    quantity: Optional[int] = Field(
        default=None,
        gt=0,
        description="Number of option units (optional, for total P&L calculation).",
    )

    @field_validator("entry_premium", "target_profit_percent")
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        """Reject non-finite numeric values."""
        if not math.isfinite(v):
            raise ValueError("Value must be a finite number.")
        return v


class RequiredSpotRequest(BaseModel):
    """Request schema for the /options/required-spot endpoint.

    Reverse-solves the underlying spot required for the option to
    reach a specified target premium.
    """

    underlying_symbol: str = Field(
        default="NIFTY",
        description="Underlying index symbol.",
    )
    strike_price: float = Field(
        ...,
        gt=0,
        description="Strike price of the option in index points.",
    )
    option_type: OptionType = Field(
        ...,
        description="Option type: 'CE' for Call, 'PE' for Put.",
    )
    target_premium: float = Field(
        ...,
        gt=0,
        description="Target option premium to solve for.",
    )
    expiry: datetime = Field(
        ...,
        description="Expiry date and time as a timezone-aware ISO 8601 timestamp.",
    )
    time_to_expiry_minutes: float = Field(
        ...,
        gt=0,
        description="Remaining time to expiry in minutes.",
    )
    implied_volatility_percent: float = Field(
        ...,
        ge=0.01,
        le=500.0,
        description="Annualized implied volatility in percentage.",
    )
    risk_free_rate_percent: float = Field(
        default=7.0,
        ge=0.0,
        le=100.0,
        description="Annual risk-free interest rate in percentage.",
    )
    dividend_yield_percent: float = Field(
        default=1.2,
        ge=0.0,
        le=50.0,
        description="Annual continuous dividend yield in percentage.",
    )

    @field_validator("expiry")
    @classmethod
    def expiry_must_be_timezone_aware(cls, v: datetime) -> datetime:
        """Reject naive (timezone-unaware) expiry timestamps."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Expiry must be a timezone-aware datetime (include timezone offset).")
        return v

    @field_validator(
        "strike_price",
        "target_premium",
        "time_to_expiry_minutes",
        "implied_volatility_percent",
        "risk_free_rate_percent",
        "dividend_yield_percent",
    )
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        """Reject non-finite numeric values."""
        if not math.isfinite(v):
            raise ValueError("Value must be a finite number.")
        return v


class GreeksRequest(BaseModel):
    """Request schema for the /options/greeks endpoint.

    Calculates Black-Scholes-Merton Greeks for a supplied contract
    and market assumptions.
    """

    underlying_symbol: str = Field(
        default="NIFTY",
        description="Underlying index symbol.",
    )
    spot_price: float = Field(
        ...,
        gt=0,
        description="Current underlying spot price in index points.",
    )
    strike_price: float = Field(
        ...,
        gt=0,
        description="Strike price of the option in index points.",
    )
    option_type: OptionType = Field(
        ...,
        description="Option type: 'CE' for Call, 'PE' for Put.",
    )
    expiry: datetime = Field(
        ...,
        description="Expiry date and time as a timezone-aware ISO 8601 timestamp.",
    )
    implied_volatility_percent: float = Field(
        ...,
        ge=0.01,
        le=500.0,
        description="Annualized implied volatility in percentage.",
    )
    risk_free_rate_percent: float = Field(
        default=7.0,
        ge=0.0,
        le=100.0,
        description="Annual risk-free interest rate in percentage.",
    )
    dividend_yield_percent: float = Field(
        default=1.2,
        ge=0.0,
        le=50.0,
        description="Annual continuous dividend yield in percentage.",
    )

    @field_validator("expiry")
    @classmethod
    def expiry_must_be_timezone_aware(cls, v: datetime) -> datetime:
        """Reject naive (timezone-unaware) expiry timestamps."""
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Expiry must be a timezone-aware datetime (include timezone offset).")
        return v

    @field_validator(
        "spot_price",
        "strike_price",
        "implied_volatility_percent",
        "risk_free_rate_percent",
        "dividend_yield_percent",
    )
    @classmethod
    def must_be_finite(cls, v: float) -> float:
        """Reject non-finite numeric values."""
        if not math.isfinite(v):
            raise ValueError("Value must be a finite number.")
        return v


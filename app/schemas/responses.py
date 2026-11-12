"""Pydantic v2 response schemas for the NIFTY Options Pricing API.

All response models use clear field descriptions with units documented.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str = Field(description="Service health status.")
    version: str = Field(description="API version string.")
    service: str = Field(description="Service name.")
    timestamp: datetime = Field(description="Current server timestamp (UTC).")


class ScenarioPremium(BaseModel):
    """Premium estimate under a specific IV scenario."""

    scenario_name: str = Field(description="Name of the scenario (e.g., 'conservative', 'base', 'optimistic').")
    iv_used_percent: float = Field(description="Implied volatility used for this scenario, in percentage.")
    estimated_premium: float = Field(description="Estimated option premium under this scenario.")
    description: str = Field(description="Human-readable description of the scenario.")


class GreeksResult(BaseModel):
    """Black-Scholes-Merton Greeks for an option."""

    delta: Optional[float] = Field(
        default=None,
        description="Delta: premium change per one-point underlying move.",
    )
    gamma: Optional[float] = Field(
        default=None,
        description="Gamma: change in delta per one-point underlying move.",
    )
    theta: Optional[float] = Field(
        default=None,
        description="Theta: premium change per calendar day (annual derivative / 365).",
    )
    vega: Optional[float] = Field(
        default=None,
        description="Vega: premium change for a one-percentage-point IV change.",
    )
    rho: Optional[float] = Field(
        default=None,
        description="Rho: premium change for a one-percentage-point interest rate change.",
    )


class TimeDecayComparison(BaseModel):
    """Flat-underlying time-decay comparison.

    Compares theoretical premiums at current time vs. after the expected
    holding duration, with spot and IV held constant.
    """

    current_theoretical_premium: float = Field(
        description="Theoretical premium at current spot and current time to expiry.",
    )
    future_theoretical_premium: float = Field(
        description="Theoretical premium at same spot and IV, with time reduced by holding duration.",
    )
    theoretical_decay: float = Field(
        description="Difference: current_theoretical_premium - future_theoretical_premium.",
    )
    holding_duration_minutes: float = Field(
        description="Expected holding duration in minutes.",
    )


class EstimateResponse(BaseModel):
    """Response from the /options/estimate endpoint."""

    model_name: str = Field(description="Pricing model used (e.g., 'Black-Scholes-Merton').")
    model_version: str = Field(description="Version of the pricing model implementation.")
    input_assumptions: Dict[str, Any] = Field(
        description="Input assumptions and units used for the calculation.",
    )
    target_spot: float = Field(description="User-specified target underlying spot price.")
    estimated_target_arrival: datetime = Field(
        description="Estimated time when the underlying reaches the target spot (UTC).",
    )
    remaining_time_to_expiry_years: float = Field(
        description="Remaining time to expiry at target arrival, in years (ACT/365).",
    )
    base_estimated_premium: float = Field(
        description="Base estimated option premium at target spot (IV unchanged).",
    )
    scenarios: List[ScenarioPremium] = Field(
        description="Premium estimates under different IV scenarios.",
    )
    greeks: GreeksResult = Field(
        description="Black-Scholes-Merton Greeks at the target conditions.",
    )
    gross_profit_per_unit: float = Field(
        description="Gross profit per unit: estimated_premium - entry_premium.",
    )
    gross_pnl: float = Field(
        description="Gross P&L: gross_profit_per_unit * quantity.",
    )
    gross_roi_percent: float = Field(
        description="Gross ROI: (gross_profit_per_unit / entry_premium) * 100.",
    )
    time_decay_comparison: TimeDecayComparison = Field(
        description="Flat-underlying time-decay comparison.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about assumptions, edge cases, or limitations.",
    )
    disclaimer: str = Field(
        default=(
            "This is a theoretical estimate based on the Black-Scholes-Merton model "
            "under stated assumptions. It is not financial advice and does not guarantee "
            "any executable price or profit. Actual option prices may differ due to "
            "changes in implied volatility, liquidity, bid-ask spread, market conditions, "
            "and other factors. Gross figures exclude brokerage, taxes, exchange fees, "
            "slippage, and other charges."
        ),
        description="Standard disclaimer about theoretical estimates.",
    )
    calculation_timestamp: datetime = Field(
        description="Timestamp when the calculation was performed (UTC).",
    )


class TargetPriceResponse(BaseModel):
    """Response from the /options/target-price endpoint."""

    entry_premium: float = Field(description="Entry premium per unit.")
    target_profit_percent: float = Field(description="Requested gross profit percentage.")
    required_exit_premium: float = Field(
        description="Exit premium required to achieve the target profit.",
    )
    gross_profit_per_unit: float = Field(
        description="Gross profit per unit: required_exit_premium - entry_premium.",
    )
    gross_pnl: Optional[float] = Field(
        default=None,
        description="Gross P&L if quantity was supplied: gross_profit_per_unit * quantity.",
    )
    quantity: Optional[int] = Field(
        default=None,
        description="Number of option units, if supplied.",
    )
    note: str = Field(
        default=(
            "This is a premium target calculation, not a forecast of the underlying spot. "
            "The required exit premium represents the price at which you would need to sell "
            "the option to achieve the stated gross profit. Gross figures exclude brokerage, "
            "taxes, exchange fees, slippage, and other charges."
        ),
        description="Explanatory note about the calculation.",
    )


class RequiredSpotResponse(BaseModel):
    """Response from the /options/required-spot endpoint."""

    required_spot: Optional[float] = Field(
        default=None,
        description="Required underlying spot price for the option to reach the target premium. "
        "Null if no solution found in the search domain.",
    )
    target_premium: float = Field(description="Target option premium to solve for.")
    solver_status: str = Field(
        description="Solver outcome: 'solution_found', 'no_solution_in_search_range', or error status.",
    )
    model_assumptions: Dict[str, Any] = Field(
        description="Model assumptions used for the reverse solve.",
    )
    message: str = Field(
        description="Human-readable explanation of the solver result.",
    )


class GreeksResponse(BaseModel):
    """Response from the /options/greeks endpoint."""

    spot_price: float = Field(description="Underlying spot price used.")
    strike_price: float = Field(description="Strike price of the option.")
    option_type: str = Field(description="Option type: 'CE' or 'PE'.")
    time_to_expiry_years: float = Field(
        description="Time to expiry in years (ACT/365).",
    )
    iv_percent: float = Field(
        description="Implied volatility in percentage.",
    )
    greeks: GreeksResult = Field(
        description="Calculated Greeks with documented units.",
    )
    calculation_timestamp: datetime = Field(
        description="Timestamp when the calculation was performed (UTC).",
    )


class ErrorResponse(BaseModel):
    """Consistent error response schema."""

    error_code: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Human-readable error message.")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details, if available.",
    )


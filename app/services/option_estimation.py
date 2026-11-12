"""Option estimation service.

Orchestrates the Black-Scholes-Merton pricing engine, Greeks calculation,
IV scenario generation, flat-underlying time-decay comparison, reverse solver,
and P&L computation.

API route functions delegate to this service rather than performing calculations directly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.pricing.black_scholes import black_scholes_price
from app.pricing.greeks import calculate_greeks
from app.pricing.scenarios import generate_iv_scenarios
from app.pricing.solver import solve_required_spot
from app.pricing.time_utils import (
    calculate_target_and_remaining_time,
    to_year_fraction,
)
from app.schemas.requests import (
    EstimateRequest,
    GreeksRequest,
    RequiredSpotRequest,
    TargetPriceRequest,
)
from app.schemas.responses import (
    EstimateResponse,
    GreeksResponse,
    GreeksResult,
    RequiredSpotResponse,
    TargetPriceResponse,
    TimeDecayComparison,
)


MODEL_NAME = "Black-Scholes-Merton"
MODEL_VERSION = "0.1.0"


def estimate_option_target(
    request: EstimateRequest,
    calculation_time: Optional[datetime] = None,
) -> EstimateResponse:
    """Perform a complete option target price and P&L estimation."""
    calc_now = calculation_time or datetime.now(request.expiry.tzinfo or timezone.utc)

    # 1. Time conversion and target arrival
    target_arrival, current_t_years, remaining_t_years = calculate_target_and_remaining_time(
        expiry=request.expiry,
        expected_time_to_target_minutes=request.expected_time_to_target_minutes,
        calculation_time=calc_now,
        allow_expiry_valuation=False,
    )

    # 2. Convert percentages to decimal
    r_decimal = request.risk_free_rate_percent / 100.0
    q_decimal = request.dividend_yield_percent / 100.0
    iv_decimal = request.implied_volatility_percent / 100.0

    # 3. Base estimated premium at target spot and target time
    base_estimated_premium = black_scholes_price(
        spot=request.target_spot,
        strike=request.strike_price,
        time_to_expiry_years=remaining_t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
    )

    # 4. IV Scenarios
    iv_shift = request.iv_shift_points if request.iv_shift_points is not None else 2.0
    scenarios, scenario_warnings = generate_iv_scenarios(
        spot=request.target_spot,
        strike=request.strike_price,
        time_to_expiry_years=remaining_t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        base_iv_percent=request.implied_volatility_percent,
        option_type=request.option_type,
        shift_percentage_points=iv_shift,
    )

    # 5. Greeks at target conditions
    target_greeks = calculate_greeks(
        spot=request.target_spot,
        strike=request.strike_price,
        time_to_expiry_years=remaining_t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
    )

    # 6. Gross P&L and ROI
    gross_profit_per_unit = base_estimated_premium - request.entry_premium
    gross_pnl = gross_profit_per_unit * request.quantity
    gross_roi_percent = (gross_profit_per_unit / request.entry_premium) * 100.0

    # 7. Flat-Underlying Time-Decay Comparison
    current_theoretical_premium = black_scholes_price(
        spot=request.current_spot,
        strike=request.strike_price,
        time_to_expiry_years=current_t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
    )
    future_theoretical_premium = black_scholes_price(
        spot=request.current_spot,
        strike=request.strike_price,
        time_to_expiry_years=remaining_t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
    )
    theoretical_decay = current_theoretical_premium - future_theoretical_premium

    time_decay_comparison = TimeDecayComparison(
        current_theoretical_premium=round(current_theoretical_premium, 4),
        future_theoretical_premium=round(future_theoretical_premium, 4),
        theoretical_decay=round(theoretical_decay, 4),
        holding_duration_minutes=request.expected_time_to_target_minutes,
    )

    # 8. Compile Warnings
    warnings: List[str] = [
        f"Base scenario assumes implied volatility remains constant at {request.implied_volatility_percent:.2f}% "
        "until target arrival.",
        "Model prices are theoretical estimates under continuous Black-Scholes-Merton assumptions. "
        "Actual execution and market bid-ask quotes can vary materially.",
    ]
    warnings.extend(scenario_warnings)
    if remaining_t_years < (1.0 / (365.0 * 24.0)):
        warnings.append(
            "Less than 1 hour remaining to expiry at target arrival. "
            "Time decay and gamma acceleration may cause extreme price sensitivity."
        )

    # 9. Document Input Assumptions
    input_assumptions: Dict[str, Any] = {
        "underlying_symbol": request.underlying_symbol,
        "current_spot": request.current_spot,
        "target_spot": request.target_spot,
        "strike_price": request.strike_price,
        "option_type": request.option_type,
        "entry_premium": request.entry_premium,
        "quantity": request.quantity,
        "expiry_iso": request.expiry.isoformat(),
        "expected_time_to_target_minutes": request.expected_time_to_target_minutes,
        "implied_volatility_percent": request.implied_volatility_percent,
        "risk_free_rate_percent": request.risk_free_rate_percent,
        "dividend_yield_percent": request.dividend_yield_percent,
        "day_count_convention": "ACT/365",
        "exercise_style": "European",
    }

    return EstimateResponse(
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        input_assumptions=input_assumptions,
        target_spot=round(request.target_spot, 2),
        estimated_target_arrival=target_arrival,
        remaining_time_to_expiry_years=round(remaining_t_years, 6),
        base_estimated_premium=round(base_estimated_premium, 4),
        scenarios=scenarios,
        greeks=target_greeks,
        gross_profit_per_unit=round(gross_profit_per_unit, 4),
        gross_pnl=round(gross_pnl, 2),
        gross_roi_percent=round(gross_roi_percent, 2),
        time_decay_comparison=time_decay_comparison,
        warnings=warnings,
        calculation_timestamp=calc_now,
    )


def calculate_target_exit_price(request: TargetPriceRequest) -> TargetPriceResponse:
    """Calculate the required option exit premium to achieve a gross profit goal."""
    required_exit_premium = request.entry_premium * (1.0 + request.target_profit_percent / 100.0)
    gross_profit_per_unit = required_exit_premium - request.entry_premium
    gross_pnl = gross_profit_per_unit * request.quantity if request.quantity is not None else None

    return TargetPriceResponse(
        entry_premium=round(request.entry_premium, 4),
        target_profit_percent=round(request.target_profit_percent, 2),
        required_exit_premium=round(required_exit_premium, 4),
        gross_profit_per_unit=round(gross_profit_per_unit, 4),
        gross_pnl=round(gross_pnl, 2) if gross_pnl is not None else None,
        quantity=request.quantity,
    )


def calculate_required_spot_service(request: RequiredSpotRequest) -> RequiredSpotResponse:
    """Reverse-solve the underlying spot required to achieve target premium."""
    t_years = request.time_to_expiry_minutes / (365.0 * 24.0 * 60.0)
    r_decimal = request.risk_free_rate_percent / 100.0
    q_decimal = request.dividend_yield_percent / 100.0
    iv_decimal = request.implied_volatility_percent / 100.0

    solved_spot, status, msg = solve_required_spot(
        strike=request.strike_price,
        time_to_expiry_years=t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
        target_premium=request.target_premium,
    )

    assumptions = {
        "underlying_symbol": request.underlying_symbol,
        "strike_price": request.strike_price,
        "option_type": request.option_type,
        "target_premium": request.target_premium,
        "time_to_expiry_minutes": request.time_to_expiry_minutes,
        "time_to_expiry_years": round(t_years, 6),
        "implied_volatility_percent": request.implied_volatility_percent,
        "risk_free_rate_percent": request.risk_free_rate_percent,
        "dividend_yield_percent": request.dividend_yield_percent,
    }

    return RequiredSpotResponse(
        required_spot=round(solved_spot, 2) if solved_spot is not None else None,
        target_premium=round(request.target_premium, 4),
        solver_status=status,
        model_assumptions=assumptions,
        message=msg,
    )


def calculate_greeks_service(
    request: GreeksRequest,
    calculation_time: Optional[datetime] = None,
) -> GreeksResponse:
    """Calculate Greeks for a supplied contract and market assumptions."""
    calc_now = calculation_time or datetime.now(request.expiry.tzinfo or timezone.utc)
    t_years = to_year_fraction(calc_now, request.expiry)

    r_decimal = request.risk_free_rate_percent / 100.0
    q_decimal = request.dividend_yield_percent / 100.0
    iv_decimal = request.implied_volatility_percent / 100.0

    greeks = calculate_greeks(
        spot=request.spot_price,
        strike=request.strike_price,
        time_to_expiry_years=t_years,
        risk_free_rate=r_decimal,
        dividend_yield=q_decimal,
        volatility=iv_decimal,
        option_type=request.option_type,
    )

    return GreeksResponse(
        spot_price=round(request.spot_price, 2),
        strike_price=round(request.strike_price, 2),
        option_type=request.option_type,
        time_to_expiry_years=round(t_years, 6),
        iv_percent=round(request.implied_volatility_percent, 2),
        greeks=greeks,
        calculation_timestamp=calc_now,
    )

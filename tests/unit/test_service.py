"""Unit tests for the option estimation service layer."""

from datetime import datetime, timedelta, timezone
import pytest

from app.core.errors import ValidationError
from app.schemas.requests import EstimateRequest, TargetPriceRequest
from app.services.option_estimation import (
    estimate_option_target,
    calculate_target_exit_price,
)


@pytest.fixture
def base_estimate_request() -> EstimateRequest:
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    expiry = now + timedelta(days=14)

    return EstimateRequest(
        underlying_symbol="NIFTY",
        current_spot=24500.0,
        target_spot=24850.0,
        option_type="CE",
        strike_price=24600.0,
        entry_premium=110.50,
        quantity=50,
        expiry=expiry,
        expected_time_to_target_minutes=180.0,  # 3 hours
        implied_volatility_percent=13.5,
        risk_free_rate_percent=7.0,
        dividend_yield_percent=1.2,
        iv_shift_points=2.0,
    )


def test_estimate_option_target_call_success(base_estimate_request):
    """Test full target estimation workflow for a long Call option."""
    ist = base_estimate_request.expiry.tzinfo
    calc_time = base_estimate_request.expiry - timedelta(days=14)

    response = estimate_option_target(base_estimate_request, calculation_time=calc_time)

    # Basic metadata
    assert response.model_name == "Black-Scholes-Merton"
    assert response.target_spot == 24850.0
    assert response.remaining_time_to_expiry_years < (14.0 / 365.0)

    # Estimated target premium should be higher than entry premium since spot rose to 24850 (ITM)
    assert response.base_estimated_premium > base_estimate_request.entry_premium
    assert response.gross_profit_per_unit > 0.0
    assert response.gross_pnl == pytest.approx(response.gross_profit_per_unit * 50, rel=1e-2)
    assert response.gross_roi_percent > 0.0

    # Greeks present
    assert response.greeks.delta is not None
    assert 0.0 < response.greeks.delta < 1.0
    assert response.greeks.gamma > 0.0
    assert response.greeks.theta < 0.0

    # Scenarios present
    assert len(response.scenarios) == 3
    assert response.scenarios[0].estimated_premium < response.scenarios[1].estimated_premium
    assert response.scenarios[1].estimated_premium < response.scenarios[2].estimated_premium

    # Time decay comparison
    td = response.time_decay_comparison
    assert td.current_theoretical_premium > td.future_theoretical_premium
    assert td.theoretical_decay > 0.0
    assert td.holding_duration_minutes == 180.0

    # Warnings and disclaimer
    assert len(response.warnings) >= 1
    assert "theoretical" in response.disclaimer.lower()


def test_estimate_option_target_put_success(base_estimate_request):
    """Test target estimation workflow for a long Put option with downward spot target."""
    ist = base_estimate_request.expiry.tzinfo
    calc_time = base_estimate_request.expiry - timedelta(days=14)

    # Put option expecting spot to drop from 24500 to 24200
    base_estimate_request.option_type = "PE"
    base_estimate_request.strike_price = 24500.0
    base_estimate_request.target_spot = 24200.0
    base_estimate_request.entry_premium = 120.0

    response = estimate_option_target(base_estimate_request, calculation_time=calc_time)

    assert response.base_estimated_premium > base_estimate_request.entry_premium
    assert response.gross_profit_per_unit > 0.0
    assert -1.0 < response.greeks.delta < 0.0


def test_estimate_option_target_rejects_past_expiry(base_estimate_request):
    """Target arrival after expiry must raise ValidationError."""
    ist = base_estimate_request.expiry.tzinfo
    calc_time = base_estimate_request.expiry - timedelta(minutes=30)
    base_estimate_request.expected_time_to_target_minutes = 60.0  # 60 min > 30 min left

    with pytest.raises(ValidationError, match="must be strictly before the option expiry"):
        estimate_option_target(base_estimate_request, calculation_time=calc_time)


def test_calculate_target_exit_price():
    """Verify target price calculation for a 50% profit goal."""
    req = TargetPriceRequest(
        entry_premium=100.0,
        target_profit_percent=50.0,
        quantity=50,
    )
    res = calculate_target_exit_price(req)

    assert res.entry_premium == 100.0
    assert res.target_profit_percent == 50.0
    assert res.required_exit_premium == 150.0
    assert res.gross_profit_per_unit == 50.0
    assert res.gross_pnl == 2500.0
    assert "not a forecast" in res.note.lower()


"""Unit tests for time-to-expiry and target arrival time utilities."""

from datetime import datetime, timedelta, timezone
import pytest

from app.core.errors import ValidationError
from app.pricing.time_utils import (
    DAYS_PER_YEAR,
    ensure_timezone_aware,
    to_year_fraction,
    calculate_target_and_remaining_time,
)


def test_ensure_timezone_aware_accepts_aware():
    dt = datetime(2026, 11, 26, 15, 30, tzinfo=timezone.utc)
    res = ensure_timezone_aware(dt)
    assert res == dt


def test_ensure_timezone_aware_rejects_naive():
    dt = datetime(2026, 11, 26, 15, 30)
    with pytest.raises(ValidationError, match="must be a timezone-aware datetime"):
        ensure_timezone_aware(dt)


def test_to_year_fraction_exact_day_counts():
    tz = timezone(timedelta(hours=5, minutes=30))  # IST
    start = datetime(2026, 1, 1, 0, 0, tzinfo=tz)
    
    # 365 days later
    end_365 = start + timedelta(days=365)
    assert pytest.approx(to_year_fraction(start, end_365), rel=1e-8) == 1.0

    # 1 day later
    end_1 = start + timedelta(days=1)
    assert pytest.approx(to_year_fraction(start, end_1), rel=1e-8) == 1.0 / DAYS_PER_YEAR

    # End before or equal to start returns 0.0
    assert to_year_fraction(start, start) == 0.0
    assert to_year_fraction(end_1, start) == 0.0


def test_to_year_fraction_rejects_naive():
    tz = timezone.utc
    aware = datetime(2026, 1, 1, 0, 0, tzinfo=tz)
    naive = datetime(2026, 1, 2, 0, 0)

    with pytest.raises(ValidationError):
        to_year_fraction(aware, naive)

    with pytest.raises(ValidationError):
        to_year_fraction(naive, aware)


def test_calculate_target_and_remaining_time_valid():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime(2026, 11, 26, 9, 30, tzinfo=ist)
    expiry = datetime(2026, 11, 26, 15, 30, tzinfo=ist)  # 6 hours to expiry
    expected_minutes = 120.0  # 2 hours

    target_time, curr_t, rem_t = calculate_target_and_remaining_time(
        expiry=expiry,
        expected_time_to_target_minutes=expected_minutes,
        calculation_time=now,
    )

    assert target_time == datetime(2026, 11, 26, 11, 30, tzinfo=ist)
    assert curr_t > rem_t
    # 6 hours = 6 / 24 days = 0.25 / 365 years
    assert pytest.approx(curr_t, rel=1e-5) == (6.0 / 24.0) / 365.0
    # 4 hours remaining = 4 / 24 days = (1/6) / 365 years
    assert pytest.approx(rem_t, rel=1e-5) == (4.0 / 24.0) / 365.0


def test_calculate_target_and_remaining_time_rejects_target_past_expiry():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime(2026, 11, 26, 9, 30, tzinfo=ist)
    expiry = datetime(2026, 11, 26, 15, 30, tzinfo=ist)
    expected_minutes = 400.0  # > 6 hours (target after expiry)

    with pytest.raises(ValidationError, match="must be strictly before the option expiry"):
        calculate_target_and_remaining_time(
            expiry=expiry,
            expected_time_to_target_minutes=expected_minutes,
            calculation_time=now,
            allow_expiry_valuation=False,
        )


def test_calculate_target_and_remaining_time_rejects_calc_time_past_expiry():
    ist = timezone(timedelta(hours=5, minutes=30))
    expiry = datetime(2026, 11, 26, 15, 30, tzinfo=ist)
    past_expiry = expiry + timedelta(minutes=10)

    with pytest.raises(ValidationError, match="Calculation time is at or after the option expiry"):
        calculate_target_and_remaining_time(
            expiry=expiry,
            expected_time_to_target_minutes=60.0,
            calculation_time=past_expiry,
        )


def test_calculate_target_and_remaining_time_invalid_duration():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime(2026, 11, 26, 9, 30, tzinfo=ist)
    expiry = datetime(2026, 11, 26, 15, 30, tzinfo=ist)

    with pytest.raises(ValidationError, match="must be strictly positive"):
        calculate_target_and_remaining_time(
            expiry=expiry,
            expected_time_to_target_minutes=0.0,
            calculation_time=now,
        )


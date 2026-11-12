"""Time-to-expiry and target arrival time utilities.

Handles conversion between timestamps and year fractions using the ACT/365
day-count convention:
    T = total_seconds / (365.0 * 86400.0)

All timestamps must be timezone-aware (rejects naive datetimes) to prevent
time discrepancy bugs across time zones (e.g. UTC vs IST UTC+5:30).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.errors import ValidationError


# ACT/365 constants
DAYS_PER_YEAR = 365.0
SECONDS_PER_DAY = 86400.0
SECONDS_PER_YEAR = DAYS_PER_YEAR * SECONDS_PER_DAY


def ensure_timezone_aware(dt: datetime, field_name: str = "datetime") -> datetime:
    """Validate that a datetime object is timezone-aware.

    Args:
        dt: The datetime to check.
        field_name: Name of the field for error messaging.

    Returns:
        The validated datetime.

    Raises:
        ValidationError: If dt is timezone-naive.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValidationError(
            f"The field '{field_name}' must be a timezone-aware datetime.",
            details={"field": field_name, "value": str(dt)},
        )
    return dt


def to_year_fraction(start_time: datetime, end_time: datetime) -> float:
    """Convert the duration between two timezone-aware timestamps into years (ACT/365).

    Args:
        start_time: Start timestamp (timezone-aware).
        end_time: End timestamp (timezone-aware).

    Returns:
        Fraction of year as float. If end_time <= start_time, returns 0.0.

    Raises:
        ValidationError: If either timestamp is timezone-naive.
    """
    ensure_timezone_aware(start_time, "start_time")
    ensure_timezone_aware(end_time, "end_time")

    delta_seconds = (end_time - start_time).total_seconds()
    if delta_seconds <= 0.0:
        return 0.0

    return float(delta_seconds / SECONDS_PER_YEAR)


def calculate_target_and_remaining_time(
    expiry: datetime,
    expected_time_to_target_minutes: float,
    calculation_time: Optional[datetime] = None,
    allow_expiry_valuation: bool = False,
) -> tuple[datetime, float, float]:
    """Calculate target arrival time and remaining time to expiry.

    Args:
        expiry: Option expiry timestamp (must be timezone-aware).
        expected_time_to_target_minutes: Expected time to reach target spot in minutes (> 0).
        calculation_time: Base timestamp for calculation (defaults to current time in expiry's tz).
        allow_expiry_valuation: If True, allows target arrival exactly at expiry.

    Returns:
        tuple of:
            - target_arrival_time: timezone-aware datetime of target arrival
            - current_time_to_expiry_years: time from calculation_time to expiry in years
            - remaining_time_to_expiry_years: time from target_arrival_time to expiry in years

    Raises:
        ValidationError: If expiry is naive, time to target <= 0, or target arrival is past expiry.
    """
    ensure_timezone_aware(expiry, "expiry")

    if expected_time_to_target_minutes <= 0.0:
        raise ValidationError(
            "expected_time_to_target_minutes must be strictly positive.",
            details={"expected_time_to_target_minutes": expected_time_to_target_minutes},
        )

    if calculation_time is None:
        # Default to now in the expiry's timezone
        calc_tz = expiry.tzinfo or timezone.utc
        calculation_time = datetime.now(calc_tz)
    else:
        ensure_timezone_aware(calculation_time, "calculation_time")

    # Current time must be strictly before expiry
    if calculation_time >= expiry:
        raise ValidationError(
            "Calculation time is at or after the option expiry.",
            details={"calculation_time": calculation_time.isoformat(), "expiry": expiry.isoformat()},
        )

    target_arrival_time = calculation_time + timedelta(minutes=expected_time_to_target_minutes)

    # Validate target arrival against expiry
    if allow_expiry_valuation:
        if target_arrival_time > expiry:
            raise ValidationError(
                "Target arrival time is after the option expiry.",
                details={
                    "target_arrival_time": target_arrival_time.isoformat(),
                    "expiry": expiry.isoformat(),
                },
            )
    else:
        if target_arrival_time >= expiry:
            raise ValidationError(
                "Target arrival time must be strictly before the option expiry.",
                details={
                    "target_arrival_time": target_arrival_time.isoformat(),
                    "expiry": expiry.isoformat(),
                },
            )

    current_t_years = to_year_fraction(calculation_time, expiry)
    remaining_t_years = to_year_fraction(target_arrival_time, expiry)

    return target_arrival_time, current_t_years, remaining_t_years

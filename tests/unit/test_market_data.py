"""Unit tests for market data providers and stale data handling."""

from datetime import datetime, timedelta, timezone
import pytest

from app.core.errors import MarketDataError
from app.market_data import (
    ManualMarketDataProvider,
    get_market_data_provider,
    is_quote_stale,
)
from app.market_data.providers.dhan import DhanHQProvider


def test_manual_provider_spot_quote_no_fake_data():
    """Manual provider must return manual status and None price, never fabricated data."""
    provider = ManualMarketDataProvider()
    quote = provider.get_spot_quote("NIFTY")

    assert quote.symbol == "NIFTY"
    assert quote.price is None
    assert quote.source == "manual"
    assert quote.is_stale is False
    assert "manual mode" in quote.message.lower()


def test_manual_provider_option_quote_no_fake_data():
    """Manual provider option quote must not fabricate premium or IV."""
    provider = ManualMarketDataProvider()
    quote = provider.get_option_quote("NIFTY24600CE")

    assert quote.premium is None
    assert quote.implied_volatility is None
    assert quote.source == "manual"
    assert "manual mode" in quote.message.lower()


def test_is_quote_stale_detection():
    """Stale quote detector returns False for recent quotes and True for old quotes."""
    now = datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc)

    # 10 seconds ago -> fresh (under 60s threshold)
    fresh_time = now - timedelta(seconds=10)
    assert is_quote_stale(fresh_time, threshold_seconds=60.0, current_time=now) is False

    # 65 seconds ago -> stale (exceeds 60s threshold)
    stale_time = now - timedelta(seconds=65)
    assert is_quote_stale(stale_time, threshold_seconds=60.0, current_time=now) is True


def test_dhan_provider_unconfigured_credentials_raises_market_data_error():
    """DhanHQ provider without credentials raises safe MarketDataError without leaking."""
    provider = DhanHQProvider(client_id=None, access_token=None)

    with pytest.raises(MarketDataError) as exc_info:
        provider.get_spot_quote("NIFTY")

    err = exc_info.value
    assert "unconfigured" in err.message.lower()
    assert err.details["provider"] == "DhanHQ"
    # Ensure no secrets leak in details
    assert "access_token" not in str(err.details)
    assert "client_id" not in str(err.details)


def test_market_data_factory_defaults_to_manual():
    """Factory returns ManualMarketDataProvider by default."""
    provider = get_market_data_provider()
    assert isinstance(provider, ManualMarketDataProvider)

    provider_explicit = get_market_data_provider("manual")
    assert isinstance(provider_explicit, ManualMarketDataProvider)

    provider_dhan = get_market_data_provider("dhan")
    assert isinstance(provider_dhan, DhanHQProvider)

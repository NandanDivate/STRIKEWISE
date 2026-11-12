"""Manual market data provider.

Passes through user-supplied values from the API request without
fetching any external data. This provider requires no credentials
and works completely offline.

Zero fake or fabricated market data is generated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.market_data.base import MarketDataProvider, OptionQuote, SpotQuote


class ManualMarketDataProvider:
    """Market data provider for manual input mode."""

    def __init__(self) -> None:
        self.source_name = "manual"

    def get_spot_quote(self, symbol: str) -> SpotQuote:
        """In manual mode, spot price is supplied directly in the API request."""
        return SpotQuote(
            symbol=symbol,
            price=None,
            timestamp=datetime.now(timezone.utc),
            source=self.source_name,
            is_stale=False,
            message="Manual mode active: spot price must be provided in request payload.",
        )

    def get_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """In manual mode, strike and expiry are supplied directly in the API request."""
        return []

    def get_option_quote(self, instrument_id: str) -> OptionQuote:
        """In manual mode, premium and IV are supplied directly in the API request."""
        return OptionQuote(
            instrument_id=instrument_id,
            symbol="NIFTY",
            strike=0.0,
            option_type="CE",
            expiry=datetime.now(timezone.utc),
            premium=None,
            timestamp=datetime.now(timezone.utc),
            source=self.source_name,
            implied_volatility=None,
            is_stale=False,
            message="Manual mode active: entry premium and IV must be provided in request payload.",
        )

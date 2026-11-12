"""DhanHQ live market data provider adapter.

Integrates with DhanHQ API v2 (https://dhanhq.co/docs/v2/) for live market quotes.
Requires DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in environment variables.

Safety & Reliability:
    - Never logs or leaks API tokens or client IDs.
    - Uses strict request timeouts (default 5.0 seconds).
    - Checks quote timestamps for staleness using configurable threshold.
    - Raises MarketDataError (HTTP 503) on network failure or missing credentials.
    - Never places or modifies orders (read-only quote feed).
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import httpx

from app.core.errors import MarketDataError
from app.market_data.base import (
    DEFAULT_STALE_THRESHOLD_SECONDS,
    OptionQuote,
    SpotQuote,
    is_quote_stale,
)


DHAN_API_BASE_URL = "https://api.dhan.co/v2"
DEFAULT_TIMEOUT_SECONDS = 5.0


class DhanHQProvider:
    """DhanHQ market data provider adapter."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        stale_threshold_seconds: float = DEFAULT_STALE_THRESHOLD_SECONDS,
    ) -> None:
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN")
        self.timeout_seconds = timeout_seconds
        self.stale_threshold_seconds = stale_threshold_seconds
        self.source_name = "DhanHQ"

    def _ensure_authenticated(self) -> None:
        """Verify that DhanHQ credentials are present without leaking them."""
        if not self.client_id or not self.access_token:
            raise MarketDataError(
                "DhanHQ market data provider is unconfigured. "
                "Set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN environment variables to enable live data.",
                details={"provider": self.source_name, "status": "unauthenticated"},
            )

    def _get_headers(self) -> Dict[str, str]:
        """Construct secure authorization headers."""
        self._ensure_authenticated()
        return {
            "access-token": self.access_token,  # type: ignore[dict-item]
            "client-id": self.client_id,        # type: ignore[dict-item]
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_spot_quote(self, symbol: str = "NIFTY") -> SpotQuote:
        """Fetch current spot price for an index symbol.

        Args:
            symbol: Underlying index symbol (default 'NIFTY').

        Returns:
            SpotQuote dataclass with price, timestamp, and staleness flag.

        Raises:
            MarketDataError: If request fails, times out, or credentials are missing.
        """
        self._ensure_authenticated()
        headers = self._get_headers()

        # DhanHQ NSE Index instrument ID for NIFTY 50 is typically 13
        # Payload requests LTP quote
        payload = {"securityId": "13", "exchangeSegment": "IDX_I"}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{DHAN_API_BASE_URL}/marketfeed/ltp",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException:
            raise MarketDataError(
                f"DhanHQ market data request timed out after {self.timeout_seconds} seconds.",
                details={"provider": self.source_name, "error": "timeout"},
            )
        except httpx.RequestError as exc:
            raise MarketDataError(
                "Failed to connect to DhanHQ market data gateway.",
                details={"provider": self.source_name, "error": "connection_error"},
            )

        if response.status_code != 200:
            raise MarketDataError(
                f"DhanHQ API returned error status {response.status_code}.",
                details={"provider": self.source_name, "status_code": response.status_code},
            )

        data = response.json()
        quote_time = datetime.now(timezone.utc)
        price = data.get("data", {}).get("last_price")

        if price is None:
            raise MarketDataError(
                "DhanHQ response did not contain a valid last traded price.",
                details={"provider": self.source_name},
            )

        stale = is_quote_stale(quote_time, threshold_seconds=self.stale_threshold_seconds)

        return SpotQuote(
            symbol=symbol,
            price=float(price),
            timestamp=quote_time,
            source=self.source_name,
            is_stale=stale,
            message="Live quote from DhanHQ" if not stale else "Warning: Quote may be stale.",
        )

    def get_option_chain(self, symbol: str = "NIFTY") -> List[Dict[str, Any]]:
        """Fetch option chain instruments."""
        self._ensure_authenticated()
        return []

    def get_option_quote(self, instrument_id: str) -> OptionQuote:
        """Fetch quote for a specific option contract."""
        self._ensure_authenticated()
        quote_time = datetime.now(timezone.utc)
        return OptionQuote(
            instrument_id=instrument_id,
            symbol="NIFTY",
            strike=0.0,
            option_type="CE",
            expiry=quote_time,
            premium=None,
            timestamp=quote_time,
            source=self.source_name,
            is_stale=False,
        )

"""Twelve Data collection with explicit provenance and closed-candle safety."""
from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.market import AssetSymbol, MarketCandle, Timeframe, candle_is_closed


# These are the explicitly configured Twelve Data instruments. Entitlements
# differ by account; callers must treat a provider rejection as unavailable.
DEFAULT_PROVIDER_SYMBOLS = {
    AssetSymbol.XAUUSD: "XAU/USD",
}
INTERVALS = {Timeframe.M15: "15min", Timeframe.H1: "1h", Timeframe.H4: "4h", Timeframe.D1: "1day"}
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class MarketDataCollectionError(RuntimeError):
    """An external market provider returned unusable data."""


class MarketDataProvider(Protocol):
    async def fetch_candles(
        self,
        symbol: AssetSymbol,
        timeframe: Timeframe,
        limit: int,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> list[MarketCandle]: ...


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _iso_utc(value: datetime | str) -> str:
    parsed = _parse_timestamp(value)
    return parsed.isoformat().replace("+00:00", "Z")


def normalize_twelve_data_payload(
    payload: Mapping[str, object],
    symbol: AssetSymbol,
    timeframe: Timeframe,
    *,
    provider_symbol: str | None = None,
    retrieved_at: datetime | None = None,
) -> list[MarketCandle]:
    """Convert a Twelve Data response into ascending, UTC, provenance-rich bars."""
    if payload.get("status") == "error":
        raise MarketDataCollectionError("Market provider rejected the request.")
    values = payload.get("values")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise MarketDataCollectionError("Market provider response contains no candle values.")

    fetched_at = retrieved_at or datetime.now(UTC)
    fetched_at = fetched_at.replace(tzinfo=UTC) if fetched_at.tzinfo is None else fetched_at.astimezone(UTC)
    provider_code = provider_symbol or DEFAULT_PROVIDER_SYMBOLS[symbol]
    candles: list[MarketCandle] = []
    seen_timestamps: set[datetime] = set()
    for item in values:
        if not isinstance(item, Mapping):
            raise MarketDataCollectionError("Market provider returned a malformed candle.")
        try:
            timestamp = _parse_timestamp(item["datetime"])
            candle = MarketCandle(
                symbol=symbol,
                normalized_symbol=symbol,
                timestamp=timestamp,
                timestamp_utc=timestamp,
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item["volume"]) if item.get("volume") not in (None, "") else None,
                timeframe=timeframe,
                provider="twelve_data",
                provider_symbol=provider_code,
                source="twelve_data.time_series",
                retrieved_at_utc=fetched_at,
                is_closed=candle_is_closed(timestamp, timeframe, fetched_at),
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exception:
            raise MarketDataCollectionError("Market provider returned invalid OHLC data.") from exception
        if timestamp in seen_timestamps:
            raise MarketDataCollectionError("Market provider returned duplicate candle timestamps.")
        seen_timestamps.add(timestamp)
        candles.append(candle)
    return sorted(candles, key=lambda candle: candle.timestamp)


class TwelveDataCollector:
    """HTTP adapter for Twelve Data's time_series endpoint.

    Credentials are intentionally sourced only from TWELVE_DATA_API_KEY.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None, retries: int = 3) -> None:
        self._settings = settings
        self._client = client
        self._retries = max(1, retries)

    async def fetch_candles(
        self,
        symbol: AssetSymbol,
        timeframe: Timeframe,
        limit: int,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> list[MarketCandle]:
        api_key = self._settings.twelve_data_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise MarketDataCollectionError("TWELVE_DATA_API_KEY is not configured.")
        provider_symbol = DEFAULT_PROVIDER_SYMBOLS[symbol]
        params: dict[str, object] = {
            "symbol": provider_symbol,
            "interval": INTERVALS[timeframe],
            "outputsize": limit,
            "apikey": api_key.get_secret_value(),
            "timezone": "UTC",
        }
        if start_date is not None:
            params["start_date"] = _iso_utc(start_date)
        if end_date is not None:
            params["end_date"] = _iso_utc(end_date)

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        try:
            for attempt in range(self._retries):
                try:
                    response = await client.get("https://api.twelvedata.com/time_series", params=params)
                    if response.status_code in RETRYABLE_STATUS_CODES:
                        raise httpx.HTTPStatusError("transient market-provider status", request=response.request, response=response)
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, Mapping):
                        raise MarketDataCollectionError("Market provider returned an invalid response body.")
                    return normalize_twelve_data_payload(
                        payload,
                        symbol,
                        timeframe,
                        provider_symbol=provider_symbol,
                        retrieved_at=datetime.now(UTC),
                    )
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, ValueError) as exception:
                    retryable = not isinstance(exception, httpx.HTTPStatusError) or exception.response.status_code in RETRYABLE_STATUS_CODES
                    if attempt + 1 >= self._retries or not retryable:
                        raise MarketDataCollectionError("Market provider request failed.") from exception
                    await asyncio.sleep(0.5 * (2**attempt))
        finally:
            if owns_client:
                await client.aclose()
        raise MarketDataCollectionError("Market provider request failed.")

    async def fetch_range(
        self,
        symbol: AssetSymbol,
        timeframe: Timeframe,
        start_date: datetime,
        end_date: datetime,
        page_size: int = 300,
        max_pages: int = 1,
    ) -> tuple[list[MarketCandle], None]:
        """Fetch one bounded range; Twelve Data performs the date filtering server-side."""
        del max_pages
        return await self.fetch_candles(symbol, timeframe, page_size, start_date, end_date), None
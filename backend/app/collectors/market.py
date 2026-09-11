"""Replaceable market-data collectors and strict provider payload normalization."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Protocol

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.market import AssetSymbol, MarketCandle, Timeframe


DEFAULT_PROVIDER_SYMBOLS = {
    AssetSymbol.XAUUSD: "XAU/USD",
    AssetSymbol.US100: "NDX",
    AssetSymbol.EURUSD: "EUR/USD",
    AssetSymbol.DXY: "DXY",
    AssetSymbol.GBPUSD: "GBP/USD",
    AssetSymbol.USDJPY: "USD/JPY",
}
INTERVALS = {Timeframe.M15: "15min", Timeframe.H1: "1h", Timeframe.H4: "4h", Timeframe.D1: "1day"}


class MarketDataCollectionError(RuntimeError):
    """An external market provider returned unusable data."""


class MarketDataProvider(Protocol):
    async def fetch_candles(self, symbol: AssetSymbol, timeframe: Timeframe, limit: int) -> list[MarketCandle]: ...


def _parse_timestamp(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def normalize_twelve_data_payload(
    payload: Mapping[str, object], symbol: AssetSymbol, timeframe: Timeframe
) -> list[MarketCandle]:
    """Convert a Twelve Data time_series response into validated, ascending candles."""
    if payload.get("status") == "error":
        raise MarketDataCollectionError("Market provider rejected the request.")
    values = payload.get("values")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise MarketDataCollectionError("Market provider response contains no candle values.")

    candles: list[MarketCandle] = []
    seen_timestamps: set[datetime] = set()
    for item in values:
        if not isinstance(item, Mapping):
            raise MarketDataCollectionError("Market provider returned a malformed candle.")
        try:
            timestamp = _parse_timestamp(item["datetime"])
            candle = MarketCandle(
                symbol=symbol,
                timestamp=timestamp,
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
                volume=float(item["volume"]) if item.get("volume") not in (None, "") else None,
                timeframe=timeframe,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exception:
            raise MarketDataCollectionError("Market provider returned invalid OHLC data.") from exception
        if timestamp in seen_timestamps:
            raise MarketDataCollectionError("Market provider returned duplicate candle timestamps.")
        seen_timestamps.add(timestamp)
        candles.append(candle)
    return sorted(candles, key=lambda candle: candle.timestamp)


class TwelveDataCollector:
    """HTTP adapter for Twelve Data's documented time_series endpoint."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def fetch_candles(
        self, symbol: AssetSymbol, timeframe: Timeframe, limit: int
    ) -> list[MarketCandle]:
        api_key = self._settings.market_data_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise MarketDataCollectionError("MARKET_DATA_API_KEY is not configured.")
        provider_symbol = DEFAULT_PROVIDER_SYMBOLS[symbol]
        params = {
            "symbol": provider_symbol,
            "interval": INTERVALS[timeframe],
            "outputsize": limit,
            "apikey": api_key.get_secret_value(),
            "timezone": "UTC",
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        try:
            response = await client.get("https://api.twelvedata.com/time_series", params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exception:
            raise MarketDataCollectionError("Market provider request failed.") from exception
        finally:
            if owns_client:
                await client.aclose()
        if not isinstance(payload, Mapping):
            raise MarketDataCollectionError("Market provider returned an invalid response body.")
        return normalize_twelve_data_payload(payload, symbol, timeframe)
"""Schemas for normalized market data and market-overview responses."""

from datetime import UTC, datetime, timedelta
from enum import Enum

from pydantic import Field, model_validator

from .base import APIModel


class AssetSymbol(str, Enum):
    XAUUSD = "XAUUSD"


class Timeframe(str, Enum):
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


TIMEFRAME_DELTAS = {
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4),
    Timeframe.D1: timedelta(days=1),
}


def candle_is_closed(timestamp: datetime, timeframe: Timeframe, retrieved_at: datetime | None = None) -> bool:
    """A candle is valid for inference only after its full interval elapsed."""
    checked_at = retrieved_at or datetime.now(UTC)
    timestamp_utc = timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
    checked_utc = checked_at.replace(tzinfo=UTC) if checked_at.tzinfo is None else checked_at.astimezone(UTC)
    return timestamp_utc + TIMEFRAME_DELTAS[timeframe] <= checked_utc


class MarketCandle(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float | None = Field(default=None, ge=0)
    timeframe: Timeframe
    normalized_symbol: AssetSymbol | None = None
    provider: str | None = None
    provider_symbol: str | None = None
    timestamp_utc: datetime | None = None
    retrieved_at_utc: datetime | None = None
    source: str | None = None
    is_closed: bool | None = None

    @model_validator(mode="after")
    def validate_price_range(self) -> "MarketCandle":
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("OHLC values must be contained within the low/high range")
        return self


class MarketSnapshot(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    price: float = Field(gt=0)
    daily_change_percent: float | None
    previous_daily_close: float | None = None
    points_change: float | None = None
    timeframe: Timeframe
    is_stale: bool | None = None
    retrieved_at_utc: datetime | None = None


class MarketOverviewResponse(APIModel):
    items: list[MarketSnapshot]
    generated_at: datetime


class MarketDetailResponse(APIModel):
    symbol: AssetSymbol
    candles: list[MarketCandle]
    generated_at: datetime
    indicators_as_of: datetime | None = None
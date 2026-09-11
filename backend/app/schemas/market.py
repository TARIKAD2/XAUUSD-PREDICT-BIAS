"""Schemas for normalized market data and market-overview responses."""

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from .base import APIModel


class AssetSymbol(str, Enum):
    XAUUSD = "XAUUSD"
    US100 = "US100"
    EURUSD = "EURUSD"
    DXY = "DXY"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"


class Timeframe(str, Enum):
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class MarketCandle(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float | None = Field(default=None, ge=0)
    timeframe: Timeframe

    @model_validator(mode="after")
    def validate_price_range(self) -> "MarketCandle":
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("OHLC values must be contained within the low/high range")
        return self


class MarketSnapshot(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    price: float = Field(gt=0)
    daily_change_percent: float
    timeframe: Timeframe


class MarketOverviewResponse(APIModel):
    items: list[MarketSnapshot]
    generated_at: datetime


class MarketDetailResponse(APIModel):
    symbol: AssetSymbol
    candles: list[MarketCandle]
    generated_at: datetime
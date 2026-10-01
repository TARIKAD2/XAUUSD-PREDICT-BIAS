"""Schemas for calculated data-quality reports."""
from datetime import datetime

from pydantic import Field

from .base import APIModel
from .market import AssetSymbol, Timeframe
from .worker import MarketWorkerStatus


class SymbolDataQuality(APIModel):
    symbol: AssetSymbol
    timeframe: Timeframe
    candle_count: int = Field(ge=0)
    missing_timestamps: int = Field(ge=0)
    duplicate_timestamps: int = Field(ge=0)
    invalid_ohlc: int = Field(ge=0)
    gap_count: int = Field(ge=0)
    stale: bool
    last_timestamp: datetime | None = None
    provider_status: str
    notes: list[str] = Field(default_factory=list)
    repairs: list[str] = Field(default_factory=list)


class DataQualityResponse(APIModel):
    items: list[SymbolDataQuality]
    generated_at: datetime
    market_worker: MarketWorkerStatus | None = None

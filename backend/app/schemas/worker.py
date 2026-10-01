"""Runtime status for the quota-protected XAUUSD ingestion worker."""
from datetime import datetime

from .base import APIModel
from .market import AssetSymbol, Timeframe


class MarketWorkerStatus(APIModel):
    enabled: bool
    running: bool
    status: str
    symbol: AssetSymbol = AssetSymbol.XAUUSD
    timeframe: Timeframe = Timeframe.H1
    schedule_seconds: int
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_new_candle_at: datetime | None = None
    last_prediction_refresh_at: datetime | None = None
    last_prediction_market_as_of: datetime | None = None
    last_prediction_model_version: str | None = None
    last_error: str | None = None
    next_run_at: datetime | None = None
    last_closed_processed: int | None = None
    prediction_refreshed: bool | None = None

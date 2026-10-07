"""Market-data persistence, freshness, and read services."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo import DESCENDING

from app.collectors.market import MarketDataProvider
from app.db.client import MongoClientManager
from app.db.collections import INGESTION_STATE, MARKET_DATA
from app.db.repositories import MongoRepository
from app.schemas.market import (
    AssetSymbol,
    MarketCandle,
    MarketDetailResponse,
    MarketOverviewResponse,
    MarketSnapshot,
    TIMEFRAME_DELTAS,
    Timeframe,
    candle_is_closed,
)


MAX_DATA_AGE = {
    Timeframe.M15: timedelta(hours=2),
    Timeframe.H1: timedelta(hours=4),
    Timeframe.H4: timedelta(hours=12),
    Timeframe.D1: timedelta(days=3),
}


class MarketDataUnavailableError(RuntimeError):
    """No verified market data can currently be served."""


def freshness_status(timestamp: datetime | None, timeframe: Timeframe, now: datetime | None = None) -> tuple[bool, list[str]]:
    """Return whether a closed market candle is sufficiently recent for inference."""
    if timestamp is None:
        return False, ["No closed candle is available."]
    checked_at = now or datetime.now(UTC)
    timestamp_utc = timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
    checked_utc = checked_at.replace(tzinfo=UTC) if checked_at.tzinfo is None else checked_at.astimezone(UTC)
    age = checked_utc - timestamp_utc
    if age > MAX_DATA_AGE[timeframe]:
        return False, [f"Latest closed {timeframe.value} candle is stale by {age}."]
    return True, []


class MarketService:
    def __init__(self, manager: MongoClientManager) -> None:
        self._manager = manager
        self._repository = MongoRepository(manager, MARKET_DATA)
        self._state_repository = MongoRepository(manager, INGESTION_STATE)

    @staticmethod
    def _closed(candle: MarketCandle, now: datetime | None = None) -> bool:
        return candle.is_closed is not False and candle_is_closed(candle.timestamp, candle.timeframe, now)

    async def _watermark(self, symbol: AssetSymbol, timeframe: Timeframe) -> datetime | None:
        if not self._manager.is_connected:
            return None
        state = await self._state_repository.collection.find_one(
            {"symbol": symbol.value, "timeframe": timeframe.value},
            projection={"latest_closed_timestamp": 1},
        )
        state_ts = state.get("latest_closed_timestamp") if state else None

        # Check market_data collection to ensure watermark reflects all persisted closed candles
        market_doc = await self._repository.collection.find_one(
            {"symbol": symbol.value, "timeframe": timeframe.value, "is_closed": True},
            sort=[("timestamp", DESCENDING)],
            projection={"timestamp": 1},
        )
        market_ts = market_doc.get("timestamp") if market_doc else None

        candidates = [ts for ts in (state_ts, market_ts) if isinstance(ts, datetime)]
        if not candidates:
            return None
        max_ts = max(candidates)
        # Keep ingestion_state synchronized if market_data had advanced
        if state_ts != max_ts:
            await self._state_repository.upsert_one(
                {"symbol": symbol.value, "timeframe": timeframe.value},
                {"symbol": symbol.value, "timeframe": timeframe.value, "latest_closed_timestamp": max_ts},
            )
        return max_ts

    async def watermark(self, symbol: AssetSymbol, timeframe: Timeframe) -> datetime | None:
        """Return the last persisted closed-candle timestamp for an idempotent worker."""
        return await self._watermark(symbol, timeframe)

    async def ingest(
        self,
        collector: MarketDataProvider,
        symbol: AssetSymbol,
        timeframe: Timeframe,
        limit: int = 100,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        page_size: int = 300,
        max_pages: int = 1,
    ) -> int:
        if not self._manager.is_connected:
            raise MarketDataUnavailableError("Market data storage is unavailable.")
        watermark = await self._watermark(symbol, timeframe)
        requested_start = start_date
        if requested_start is None and watermark is not None:
            # The worker fetches strictly after the watermark, so only genuinely
            # new, already-closed intervals are considered for persistence.
            requested_start = watermark + TIMEFRAME_DELTAS[timeframe]
        if requested_start is not None and hasattr(collector, "fetch_range"):
            start_dt = datetime.fromisoformat(requested_start.replace("Z", "+00:00")) if isinstance(requested_start, str) else requested_start
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if isinstance(end_date, str) else end_date
            candles, _ = await collector.fetch_range(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_dt,
                end_date=end_dt or datetime.now(UTC),
                page_size=page_size,
                max_pages=max_pages,
            )
        else:
            candles = await collector.fetch_candles(symbol, timeframe, limit, requested_start, end_date)

        now = datetime.now(UTC)
        closed = [candle for candle in candles if self._closed(candle, now)]
        for candle in closed:
            document: dict[str, Any] = candle.model_dump(mode="python", exclude_none=True)
            document["symbol"] = candle.symbol.value
            document["normalized_symbol"] = candle.normalized_symbol.value if candle.normalized_symbol else candle.symbol.value
            document["timeframe"] = candle.timeframe.value
            document["timestamp"] = candle.timestamp
            document["timestamp_utc"] = candle.timestamp
            document["retrieved_at_utc"] = candle.retrieved_at_utc or now
            document["is_closed"] = True
            document["ingested_at"] = now
            await self._repository.upsert_one(
                {"symbol": candle.symbol.value, "timeframe": candle.timeframe.value, "timestamp": candle.timestamp},
                document,
            )
        if closed:
            latest = max(candle.timestamp for candle in closed)
            await self._state_repository.upsert_one(
                {"symbol": symbol.value, "timeframe": timeframe.value},
                {
                    "symbol": symbol.value,
                    "timeframe": timeframe.value,
                    "latest_closed_timestamp": latest,
                    "last_success_at": now,
                    "provider": closed[-1].provider or "unknown",
                    "provider_symbol": closed[-1].provider_symbol,
                },
            )
        return len(closed)

    async def _recent_closed(self, symbol: AssetSymbol, timeframe: Timeframe, limit: int) -> list[MarketCandle]:
        documents = await self._repository.find_recent(
            {"symbol": symbol.value, "timeframe": timeframe.value}, limit=max(limit * 2, 50)
        )
        candles = [MarketCandle.model_validate(document) for document in documents]
        return list(reversed([candle for candle in candles if self._closed(candle)]))[-limit:]

    async def detail(self, symbol: AssetSymbol, timeframe: Timeframe, limit: int) -> MarketDetailResponse:
        if not self._manager.is_connected:
            raise MarketDataUnavailableError("Market data storage is unavailable.")
        candles = await self._recent_closed(symbol, timeframe, limit)
        if not candles:
            raise MarketDataUnavailableError(f"No verified closed {symbol.value} market data is available.")
        indicators_as_of = candles[-1].timestamp if candles else None
        return MarketDetailResponse(symbol=symbol, candles=candles, generated_at=datetime.now(UTC), indicators_as_of=indicators_as_of)

    async def _previous_daily_close(self, symbol: AssetSymbol, timeframe: Timeframe, latest: MarketCandle) -> float | None:
        day_start = latest.timestamp.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        document = await self._repository.collection.find_one(
            {"symbol": symbol.value, "timeframe": timeframe.value, "timestamp": {"$lt": day_start}},
            sort=[("timestamp", DESCENDING)],
            projection={"close": 1, "timestamp": 1, "is_closed": 1, "timeframe": 1, "symbol": 1},
        )
        if not document:
            return None
        document = {key: value for key, value in document.items() if key != "_id"}
        candidate = MarketCandle.model_validate(document | {"open": document.get("close"), "high": document.get("close"), "low": document.get("close")})
        return candidate.close if self._closed(candidate) else None

    async def overview(self, timeframe: Timeframe) -> MarketOverviewResponse:
        if not self._manager.is_connected:
            raise MarketDataUnavailableError("Market data storage is unavailable.")
        snapshots: list[MarketSnapshot] = []
        for symbol in AssetSymbol:
            candles = await self._recent_closed(symbol, timeframe, 1)
            if not candles:
                continue
            latest = candles[-1]
            previous_daily_close = await self._previous_daily_close(symbol, timeframe, latest)
            change = ((latest.close / previous_daily_close) - 1) * 100 if previous_daily_close else None
            fresh, _ = freshness_status(latest.timestamp, timeframe)
            points_change = (latest.close - previous_daily_close) if previous_daily_close else None
            snapshots.append(
                MarketSnapshot(
                    symbol=symbol,
                    timestamp=latest.timestamp,
                    price=latest.close,
                    daily_change_percent=change,
                    previous_daily_close=previous_daily_close,
                    points_change=points_change,
                    timeframe=timeframe,
                    is_stale=not fresh,
                    retrieved_at_utc=latest.retrieved_at_utc,
                )
            )
        if not snapshots:
            raise MarketDataUnavailableError("No verified closed market data is available.")
        return MarketOverviewResponse(items=snapshots, generated_at=datetime.now(UTC))

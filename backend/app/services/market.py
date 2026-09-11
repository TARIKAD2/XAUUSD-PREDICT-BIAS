"""Market-data persistence and read services."""
from __future__ import annotations

from datetime import UTC, datetime

from app.collectors.market import MarketDataProvider
from app.db.client import MongoClientManager
from app.db.collections import MARKET_DATA
from app.db.repositories import MongoRepository
from app.schemas.market import AssetSymbol, MarketCandle, MarketDetailResponse, MarketOverviewResponse, MarketSnapshot, Timeframe


class MarketDataUnavailableError(RuntimeError):
    """No verified market data can currently be served."""


class MarketService:
    def __init__(self, manager: MongoClientManager) -> None:
        self._manager = manager
        self._repository = MongoRepository(manager, MARKET_DATA)

    async def ingest(self, collector: MarketDataProvider, symbol: AssetSymbol, timeframe: Timeframe, limit: int) -> int:
        candles = await collector.fetch_candles(symbol, timeframe, limit)
        for candle in candles:
            document = candle.model_dump(mode="python")
            document["ingested_at"] = datetime.now(UTC)
            await self._repository.upsert_one(
                {"symbol": candle.symbol.value, "timeframe": candle.timeframe.value, "timestamp": candle.timestamp},
                document,
            )
        return len(candles)

    async def detail(self, symbol: AssetSymbol, timeframe: Timeframe, limit: int) -> MarketDetailResponse:
        if not self._manager.is_connected:
            raise MarketDataUnavailableError("Market data storage is unavailable.")
        documents = await self._repository.find_recent(
            {"symbol": symbol.value, "timeframe": timeframe.value}, limit=limit
        )
        candles = [MarketCandle.model_validate(document) for document in reversed(documents)]
        if not candles:
            raise MarketDataUnavailableError(f"No verified {symbol.value} market data is available.")
        return MarketDetailResponse(symbol=symbol, candles=candles, generated_at=datetime.now(UTC))

    async def overview(self, timeframe: Timeframe) -> MarketOverviewResponse:
        if not self._manager.is_connected:
            raise MarketDataUnavailableError("Market data storage is unavailable.")
        snapshots: list[MarketSnapshot] = []
        for symbol in AssetSymbol:
            documents = await self._repository.find_recent({"symbol": symbol.value, "timeframe": timeframe.value}, limit=2)
            if not documents:
                continue
            latest = MarketCandle.model_validate(documents[0])
            prior = MarketCandle.model_validate(documents[1]) if len(documents) > 1 else latest
            change = ((latest.close / prior.close) - 1) * 100 if prior.close else 0.0
            snapshots.append(MarketSnapshot(symbol=symbol, timestamp=latest.timestamp, price=latest.close, daily_change_percent=change, timeframe=timeframe))
        if not snapshots:
            raise MarketDataUnavailableError("No verified market data is available.")
        return MarketOverviewResponse(items=snapshots, generated_at=datetime.now(UTC))
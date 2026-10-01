import asyncio
from datetime import UTC, datetime

from app.core.config import Settings
from app.db.collections import INGESTION_STATE, PREDICTIONS
from app.schemas.prediction import PredictionResponse
from app.services.ingestion_worker import XAUUSDIngestionWorker


class FakeCollection:
    def __init__(self):
        self.calls = []

    async def update_one(self, identity, update, upsert=False):
        self.calls.append((identity, update, upsert))


class FakeManager:
    def __init__(self):
        self.is_connected = True
        self.database = {
            INGESTION_STATE: FakeCollection(),
            PREDICTIONS: FakeCollection(),
        }


class FakeMarketService:
    def __init__(self, before, after):
        self.watermarks = [before, after]
        self.ingest_calls = []

    async def watermark(self, symbol, timeframe):
        return self.watermarks.pop(0)

    async def ingest(self, collector, symbol, timeframe, **kwargs):
        self.ingest_calls.append((collector, symbol, timeframe, kwargs))
        return 1


class FakePredictionService:
    def __init__(self):
        self.calls = 0

    async def one(self, symbol):
        self.calls += 1
        return PredictionResponse.model_validate({
            "symbol": symbol.value,
            "timestamp": "2026-09-17T01:01:00Z",
            "prediction_timestamp_utc": "2026-09-17T01:01:00Z",
            "market_as_of_utc": "2026-09-17T01:00:00Z",
            "direction": "BULLISH",
            "probabilities": {"bullish": 0.6, "bearish": 0.4},
            "confidence": 0.6,
            "model": "lightgbm",
            "model_version": "lightgbm-test",
        })


def test_worker_uses_hourly_quota_floor_and_persists_refreshed_prediction():
    before = datetime(2026, 9, 17, 0, tzinfo=UTC)
    after = datetime(2026, 9, 17, 1, tzinfo=UTC)
    manager = FakeManager()
    market = FakeMarketService(before, after)
    prediction = FakePredictionService()
    settings = Settings(
        market_ingestion_enabled=True,
        market_ingestion_interval_seconds=60,
        market_ingestion_limit=300,
    )
    worker = XAUUSDIngestionWorker(
        manager,
        settings,
        collector_factory=lambda *_args, **_kwargs: object(),
        market_service_factory=lambda _manager: market,
        prediction_service_factory=lambda _manager: prediction,
    )

    status = asyncio.run(worker.run_once())

    assert status["status"] == "success"
    assert status["schedule_seconds"] == 3600
    assert status["last_new_candle_at"] == after
    assert status["last_prediction_model_version"] == "lightgbm-test"
    assert prediction.calls == 1
    assert market.ingest_calls[0][3]["page_size"] == 300
    assert manager.database[PREDICTIONS].calls
    persisted = manager.database[PREDICTIONS].calls[-1]
    assert persisted[0]["market_as_of_utc"] == after
    assert persisted[1]["$set"]["prediction_timestamp_utc"] is not None


def test_disabled_worker_never_creates_a_provider_cycle():
    worker = XAUUSDIngestionWorker(FakeManager(), Settings(market_ingestion_enabled=False))

    status = asyncio.run(worker.run_once())

    assert status["status"] == "disabled"
    assert status["last_attempt_at"] is None

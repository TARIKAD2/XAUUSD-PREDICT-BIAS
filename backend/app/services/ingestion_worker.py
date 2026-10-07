"""Quota-protected lifecycle worker for new, closed XAUUSD H1 candles."""
from __future__ import annotations

import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from app.collectors.market import MarketDataCollectionError, TwelveDataCollector
from app.core.config import Settings
from app.db.collections import INGESTION_STATE, PREDICTIONS
from app.db.repositories import MongoRepository
from app.schemas.market import AssetSymbol, TIMEFRAME_DELTAS, Timeframe
from app.services.market import MarketDataUnavailableError, MarketService
from app.services.predictions import PredictionService, PredictionUnavailableError


class XAUUSDIngestionWorker:
    """Fetch, persist, and predict once per closed-candle schedule.

    One active process issues at most one bounded Twelve Data request per
    effective interval. The provider adapter supplies timeout plus transient
    retry/backoff; this worker records each outcome without retraining.
    """

    symbol = AssetSymbol.XAUUSD
    timeframe = Timeframe.H1

    def __init__(
        self,
        manager: Any,
        settings: Settings,
        *,
        collector_factory: Callable[..., Any] = TwelveDataCollector,
        market_service_factory: Callable[[Any], Any] = MarketService,
        prediction_service_factory: Callable[[Any], Any] = PredictionService,
    ) -> None:
        self.manager = manager
        self.settings = settings
        self._collector_factory = collector_factory
        self._market_service_factory = market_service_factory
        self._prediction_service_factory = prediction_service_factory
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._stopping = False
        self._interval_seconds = max(
            int(settings.market_ingestion_interval_seconds),
            int(TIMEFRAME_DELTAS[self.timeframe].total_seconds()),
        )
        self._state: dict[str, Any] = {
            "enabled": settings.market_ingestion_enabled,
            "running": False,
            "status": "idle" if settings.market_ingestion_enabled else "disabled",
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "schedule_seconds": self._interval_seconds,
            "last_attempt_at": None,
            "last_success_at": None,
            "last_new_candle_at": None,
            "latest_processed_candle_timestamp": None,
            "last_prediction_refresh_at": None,
            "last_prediction_market_as_of": None,
            "last_prediction_model_version": None,
            "last_error": None,
            "next_run_at": None,
            "prediction_refreshed": False,
        }

    def snapshot(self) -> dict[str, Any]:
        """Return JSON-safe runtime state for health and data-quality routes."""
        return dict(self._state)

    async def start(self) -> None:
        if not self.settings.market_ingestion_enabled:
            return
        if self._task is None or self._task.done():
            self._stopping = False
            self._task = asyncio.create_task(self._run(), name="xauusd-h1-ingestion")

    async def stop(self) -> None:
        if not self.settings.market_ingestion_enabled:
            return
        self._stopping = True
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._state["running"] = False
        if self.settings.market_ingestion_enabled:
            self._state["status"] = "stopped"
        await self._persist_state()

    async def _run(self) -> None:
        if getattr(self.manager, "is_connected", False):
            try:
                state_doc = await self.manager.database[INGESTION_STATE].find_one(
                    {"symbol": self.symbol.value, "timeframe": self.timeframe.value}
                )
                if state_doc and "worker_latest_processed_candle_timestamp" in state_doc:
                    self._state["latest_processed_candle_timestamp"] = state_doc["worker_latest_processed_candle_timestamp"]
            except Exception:
                pass

        while not self._stopping:
            cycle_started = datetime.now(UTC)
            await self.run_once()
            # Check every 60 seconds (or bounded interval) so newly closed H1 candles are detected promptly
            delay = min(float(self._interval_seconds), 60.0)
            next_run = cycle_started + timedelta(seconds=delay)
            self._state["next_run_at"] = next_run
            await self._persist_state()
            sleep_sec = max(0.0, (next_run - datetime.now(UTC)).total_seconds())
            try:
                await asyncio.sleep(sleep_sec)
            except asyncio.CancelledError:
                raise

    async def run_once(self) -> dict[str, Any]:
        """Execute one bounded, idempotent cycle; safe for focused verification."""
        if not self.settings.market_ingestion_enabled:
            return self.snapshot()
        if not getattr(self.manager, "is_connected", False):
            self._state.update({"status": "failed", "last_error": "MongoDB is unavailable."})
            return self.snapshot()

        async with self._lock:
            attempted_at = datetime.now(UTC)
            self._state.update({
                "running": True,
                "status": "running",
                "last_attempt_at": attempted_at,
                "last_error": None,
                "next_run_at": None,
            })
            await self._persist_state()
            market = self._market_service_factory(self.manager)
            try:
                before = await market.watermark(self.symbol, self.timeframe)
                # A single request covers at most the configured bounded window.
                # On a prolonged outage, later cycles continue from the watermark
                # rather than skipping missing closed intervals.
                window_end = None
                if before is not None:
                    window_end = min(
                        datetime.now(UTC),
                        before + TIMEFRAME_DELTAS[self.timeframe] * self.settings.market_ingestion_limit,
                    )
                collector = self._collector_factory(self.settings, retries=3)
                closed_processed = await market.ingest(
                    collector,
                    self.symbol,
                    self.timeframe,
                    limit=self.settings.market_ingestion_limit,
                    end_date=window_end,
                    page_size=self.settings.market_ingestion_limit,
                    max_pages=1,
                )
                # Keep MTF candles synchronized for multi-timeframe feature calculations
                with contextlib.suppress(Exception):
                    await market.ingest(collector, self.symbol, Timeframe.M15, limit=50)
                with contextlib.suppress(Exception):
                    await market.ingest(collector, self.symbol, Timeframe.H4, limit=10)

                after = await market.watermark(self.symbol, self.timeframe)
                refreshed = False
                last_processed = self._state.get("latest_processed_candle_timestamp")
                if after is not None and (last_processed is None or after > last_processed):
                    pred_service = self._prediction_service_factory(self.manager)
                    if hasattr(pred_service, "generate_snapshot") and hasattr(pred_service, "persist_snapshot"):
                        snapshot = await pred_service.generate_snapshot(self.symbol)
                        await pred_service.persist_snapshot(snapshot)
                        prediction = snapshot.daily
                    else:
                        prediction = await pred_service.one(self.symbol)
                        await self._persist_prediction(prediction)

                    self._state.update({
                        "latest_processed_candle_timestamp": after,
                        "last_new_candle_at": after,
                        "last_prediction_refresh_at": prediction.prediction_timestamp_utc or prediction.timestamp,
                        "last_prediction_market_as_of": prediction.market_as_of_utc,
                        "last_prediction_model_version": prediction.model_version,
                    })
                    refreshed = True
                self._state.update({
                    "running": False,
                    "status": "success",
                    "last_success_at": datetime.now(UTC),
                    "last_error": None,
                    "last_closed_processed": closed_processed,
                    "prediction_refreshed": refreshed,
                })
            except (MarketDataCollectionError, MarketDataUnavailableError, PredictionUnavailableError) as exc:
                self._state.update({"running": False, "status": "failed", "last_error": str(exc)})
            except Exception as exc:  # Keep the background task alive for a later retry cycle.
                self._state.update({"running": False, "status": "failed", "last_error": type(exc).__name__})
            await self._persist_state()
            return self.snapshot()

    async def _persist_prediction(self, prediction) -> None:
        repository = MongoRepository(self.manager, PREDICTIONS)
        document = prediction.model_dump(mode="python")
        market_as_of = prediction.market_as_of_utc or prediction.data_timestamp
        document.update({
            "symbol": prediction.symbol.value,
            "timeframe": self.timeframe.value,
            "model_version": prediction.model_version,
            "prediction_timestamp_utc": prediction.prediction_timestamp_utc or prediction.timestamp,
            "market_as_of_utc": market_as_of,
            "persisted_at": datetime.now(UTC),
        })
        await repository.upsert_one(
            {
                "symbol": prediction.symbol.value,
                "timeframe": self.timeframe.value,
                "model_version": prediction.model_version,
                "market_as_of_utc": market_as_of,
            },
            document,
        )

    async def _persist_state(self) -> None:
        if not getattr(self.manager, "is_connected", False):
            return
        document = {
            "worker_enabled": self._state["enabled"],
            "worker_running": self._state["running"],
            "worker_status": self._state["status"],
            "worker_schedule_seconds": self._state["schedule_seconds"],
            "worker_last_attempt_at": self._state["last_attempt_at"],
            "worker_last_success_at": self._state["last_success_at"],
            "worker_last_new_candle_at": self._state["last_new_candle_at"],
            "worker_latest_processed_candle_timestamp": self._state.get("latest_processed_candle_timestamp"),
            "worker_last_prediction_refresh_at": self._state["last_prediction_refresh_at"],
            "worker_last_prediction_market_as_of": self._state["last_prediction_market_as_of"],
            "worker_last_prediction_model_version": self._state["last_prediction_model_version"],
            "worker_last_error": self._state["last_error"],
            "worker_next_run_at": self._state["next_run_at"],
            "worker_updated_at": datetime.now(UTC),
        }
        await self.manager.database[INGESTION_STATE].update_one(
            {"symbol": self.symbol.value, "timeframe": self.timeframe.value},
            {"$set": document},
            upsert=True,
        )

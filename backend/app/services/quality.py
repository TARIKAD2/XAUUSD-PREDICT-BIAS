"""Calculated data-quality reports over persisted market candles."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from app.db.collections import MARKET_DATA
from app.db.repositories import MongoRepository
from app.schemas.market import AssetSymbol, Timeframe
from app.schemas.quality import DataQualityResponse, SymbolDataQuality

EXPECTED_DELTAS = {
    Timeframe.M15: timedelta(minutes=15),
    Timeframe.H1: timedelta(hours=1),
    Timeframe.H4: timedelta(hours=4),
    Timeframe.D1: timedelta(days=1),
}
STALE_AFTER = {
    Timeframe.M15: timedelta(hours=6),
    Timeframe.H1: timedelta(hours=36),
    Timeframe.H4: timedelta(days=3),
    Timeframe.D1: timedelta(days=5),
}


class DataQualityUnavailableError(RuntimeError):
    pass


class DataQualityService:
    def __init__(self, manager, worker_status=None):
        self.manager = manager
        self.repo = MongoRepository(manager, MARKET_DATA)
        self.worker_status = worker_status

    async def report(self, timeframe: Timeframe = Timeframe.H1) -> DataQualityResponse:
        if not self.manager.is_connected:
            raise DataQualityUnavailableError("Data-quality storage is unavailable.")
        items: list[SymbolDataQuality] = []
        now = datetime.now(UTC)
        expected = EXPECTED_DELTAS[timeframe]
        for symbol in AssetSymbol:
            docs = await self.repo.find_all({"symbol": symbol.value, "timeframe": timeframe.value}, limit=5000)
            notes: list[str] = []
            repairs: list[str] = []
            if not docs:
                items.append(
                    SymbolDataQuality(
                        symbol=symbol,
                        timeframe=timeframe,
                        candle_count=0,
                        missing_timestamps=0,
                        duplicate_timestamps=0,
                        invalid_ohlc=0,
                        gap_count=0,
                        stale=True,
                        last_timestamp=None,
                        provider_status="unavailable",
                        notes=["No verified candles in market_data."],
                        repairs=repairs,
                    )
                )
                continue
            frame = pd.DataFrame(docs)
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
            missing_ts = int(frame["timestamp"].isna().sum())
            if missing_ts:
                repairs.append(f"Dropped {missing_ts} rows with missing timestamps.")
                frame = frame.dropna(subset=["timestamp"])
            duplicate_count = int(len(frame) - frame.drop_duplicates(subset=["timestamp"]).shape[0])
            if duplicate_count:
                repairs.append(f"Collapsed {duplicate_count} duplicate timestamps using unique index identity.")
                frame = frame.drop_duplicates(subset=["timestamp"], keep="last")
            frame = frame.sort_values("timestamp")
            invalid = 0
            if {"open", "high", "low", "close"} <= set(frame.columns):
                invalid_mask = (frame["high"] < frame[["open", "close"]].max(axis=1)) | (
                    frame["low"] > frame[["open", "close"]].min(axis=1)
                )
                invalid = int(invalid_mask.sum())
                if invalid:
                    repairs.append(f"Excluded {invalid} invalid OHLC rows from quality-clean view; originals remain stored.")
                    frame = frame.loc[~invalid_mask]
            gaps = 0
            if len(frame) > 1:
                deltas = frame["timestamp"].diff().dropna()
                gaps = int((deltas > expected * 1.6).sum())
            last_ts = frame["timestamp"].iloc[-1].to_pydatetime() if not frame.empty else None
            stale = True if last_ts is None else (now - last_ts) > STALE_AFTER[timeframe]
            if gaps:
                notes.append(f"{gaps} spacing gaps relative to {timeframe.value}.")
            if stale:
                notes.append("Latest candle is stale versus the configured freshness window.")
            items.append(
                SymbolDataQuality(
                    symbol=symbol,
                    timeframe=timeframe,
                    candle_count=int(len(docs)),
                    missing_timestamps=missing_ts,
                    duplicate_timestamps=duplicate_count,
                    invalid_ohlc=invalid,
                    gap_count=gaps,
                    stale=stale,
                    last_timestamp=last_ts,
                    provider_status="available" if not frame.empty else "unavailable",
                    notes=notes,
                    repairs=repairs,
                )
            )
        return DataQualityResponse(items=items, generated_at=now, market_worker=self.worker_status)

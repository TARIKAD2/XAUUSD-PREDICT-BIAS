"""Backfill real closed Twelve Data candles without re-requesting stored history.

Examples:
  .venv\\Scripts\\python.exe scripts\\backfill_xauusd.py
  .venv\\Scripts\\python.exe scripts\\backfill_xauusd.py --start 2024-01-01T00:00:00Z --page-size 5000 --max-requests 2
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime

sys.path.insert(0, "backend")

from app.collectors.market import DEFAULT_PROVIDER_SYMBOLS, MarketDataCollectionError, TwelveDataCollector
from app.core.config import get_settings
from app.db.client import MongoClientManager
from app.db.collections import MARKET_DATA
from app.schemas.market import AssetSymbol, TIMEFRAME_DELTAS, Timeframe, candle_is_closed


def utc_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill real closed Twelve Data candles into MongoDB.")
    parser.add_argument("--symbol", default="XAUUSD", choices=[item.value for item in AssetSymbol])
    parser.add_argument("--timeframe", default="1h", choices=[item.value for item in Timeframe])
    parser.add_argument("--start", type=utc_timestamp, help="Inclusive UTC start, e.g. 2024-01-01T00:00:00Z.")
    parser.add_argument("--end", type=utc_timestamp, help="Exclusive UTC end; defaults to the oldest stored candle.")
    parser.add_argument("--page-size", type=int, default=5000, choices=range(2, 5001), metavar="2..5000")
    parser.add_argument("--max-requests", type=int, default=1, choices=range(1, 21), metavar="1..20")
    parser.add_argument("--request-delay", type=float, default=1.0, help="Seconds between provider requests.")
    return parser.parse_args()


async def oldest_timestamp(collection, query: dict) -> datetime | None:
    item = await collection.find_one(query, sort=[("timestamp", 1)], projection={"timestamp": 1})
    return item.get("timestamp") if item else None


async def backfill(args: argparse.Namespace) -> dict:
    symbol = AssetSymbol(args.symbol)
    timeframe = Timeframe(args.timeframe)
    settings = get_settings()
    manager = MongoClientManager(settings)
    if not await manager.connect():
        raise RuntimeError("MongoDB Atlas connection is unavailable.")
    try:
        collection = manager.database[MARKET_DATA]
        query = {"symbol": symbol.value, "timeframe": timeframe.value}
        before = await collection.count_documents(query)
        oldest_before = await oldest_timestamp(collection, query)
        end = args.end or oldest_before
        if end is None:
            raise RuntimeError("No existing watermark; specify --end for an empty collection.")
        start = args.start
        if start is not None and start >= end:
            raise ValueError("--start must be earlier than --end.")
        collector = TwelveDataCollector(settings)
        summary = {
            "symbol": symbol.value,
            "timeframe": timeframe.value,
            "provider": "twelve_data",
            "provider_symbol": DEFAULT_PROVIDER_SYMBOLS[symbol],
            "before": before,
            "oldest_before": oldest_before.isoformat() if oldest_before else None,
            "requests": 0,
            "fetched": 0,
            "inserted": 0,
            "skipped_duplicates": 0,
            "rejected_invalid_or_open": 0,
            "errors": [],
            "ranges": [],
        }
        cursor_end = end
        interval = TIMEFRAME_DELTAS[timeframe]
        for request_number in range(1, args.max_requests + 1):
            if start is not None and cursor_end <= start:
                break
            summary["requests"] += 1
            requested = {
                "start": start.isoformat() if start else None,
                "end": cursor_end.isoformat(),
                "page_size": args.page_size,
            }
            try:
                candles = await collector.fetch_candles(symbol, timeframe, args.page_size, start, cursor_end)
            except MarketDataCollectionError as exc:
                summary["errors"].append({"request": request_number, "error": str(exc)})
                summary["ranges"].append({"request": request_number, "requested": requested, "fetched": 0})
                break
            summary["fetched"] += len(candles)
            now = datetime.now(UTC)
            valid = []
            for candle in candles:
                if not candle_is_closed(candle.timestamp, timeframe, now):
                    summary["rejected_invalid_or_open"] += 1
                    continue
                valid.append(candle)
            timestamps = [item.timestamp for item in valid]
            existing = set()
            if timestamps:
                existing = {
                    row["timestamp"]
                    for row in await collection.find({**query, "timestamp": {"$in": timestamps}}, projection={"timestamp": 1}).to_list(length=len(timestamps))
                }
            new_candles = [item for item in valid if item.timestamp not in existing]
            summary["skipped_duplicates"] += len(valid) - len(new_candles)
            for candle in new_candles:
                document = candle.model_dump(mode="python", exclude_none=True)
                document.update({
                    "symbol": symbol.value,
                    "normalized_symbol": symbol.value,
                    "timeframe": timeframe.value,
                    "timestamp": candle.timestamp,
                    "timestamp_utc": candle.timestamp,
                    "retrieved_at_utc": candle.retrieved_at_utc or now,
                    "is_closed": True,
                    "ingested_at": now,
                })
                await collection.update_one(
                    {"symbol": symbol.value, "timeframe": timeframe.value, "timestamp": candle.timestamp},
                    {"$set": document},
                    upsert=True,
                )
            summary["inserted"] += len(new_candles)
            oldest_fetched = min((item.timestamp for item in candles), default=None)
            summary["ranges"].append({
                "request": request_number,
                "requested": requested,
                "fetched": len(candles),
                "inserted": len(new_candles),
                "skipped_duplicates": len(valid) - len(new_candles),
                "rejected_invalid_or_open": len(candles) - len(valid),
                "oldest_fetched": oldest_fetched.isoformat() if oldest_fetched else None,
            })
            if not candles or oldest_fetched is None or len(candles) < args.page_size:
                break
            next_end = oldest_fetched - interval
            if next_end >= cursor_end:
                summary["errors"].append({"request": request_number, "error": "Provider range did not move backward."})
                break
            cursor_end = next_end
            if request_number < args.max_requests:
                await asyncio.sleep(max(args.request_delay, 0.0))
        after = await collection.count_documents(query)
        oldest_after = await oldest_timestamp(collection, query)
        newest = await collection.find_one(query, sort=[("timestamp", -1)], projection={"timestamp": 1})
        duplicates = await collection.aggregate([
            {"$match": query},
            {"$group": {"_id": {"symbol": "$symbol", "timeframe": "$timeframe", "timestamp": "$timestamp"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]).to_list(length=1)
        invalid = await collection.count_documents({**query, "$or": [{"is_closed": {"$ne": True}}, {"timestamp_utc": {"$exists": False}}, {"provider": {"$exists": False}}, {"provider_symbol": {"$exists": False}}]})
        summary.update({
            "after": after,
            "oldest_after": oldest_after.isoformat() if oldest_after else None,
            "newest_after": newest["timestamp"].isoformat() if newest else None,
            "duplicate_identities": len(duplicates),
            "rows_missing_closed_or_provenance": invalid,
        })
        return summary
    finally:
        await manager.disconnect()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(backfill(arguments())), default=str, indent=2))
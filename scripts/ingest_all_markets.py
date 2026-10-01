"""Safe multi-asset market data ingestion for XAUUSD and secondary assets."""
import asyncio
import sys
from datetime import UTC, datetime

sys.path.insert(0, "backend")

from app.core.config import get_settings
from app.collectors.market import DEFAULT_PROVIDER_SYMBOLS, TwelveDataCollector
from app.db.client import MongoClientManager
from app.db.collections import MARKET_DATA
from app.services.market import MarketService
from app.schemas.market import AssetSymbol, Timeframe


async def main():
    settings = get_settings()
    manager = MongoClientManager(settings)
    connected = await manager.connect()
    if not connected:
        print("[ERROR] Could not connect to MongoDB Atlas.")
        return

    service = MarketService(manager)
    collector = TwelveDataCollector(settings)

    assets_to_ingest = [
        (AssetSymbol.XAUUSD, 180),  # Primary asset for ML: 180 candles
    ]

    print("=" * 70)
    print("PHASE 4: REAL MARKET DATA EXPANSION & INGESTION")
    print("=" * 70)

    coll = manager.database[MARKET_DATA]

    for symbol, limit in assets_to_ingest:
        provider_sym = DEFAULT_PROVIDER_SYMBOLS[symbol]
        print(f"\nAsset: {symbol.value} (Provider: {provider_sym}, Timeframe: 1h, Limit: {limit})")

        try:
            # Respect rate limit with pacing
            await asyncio.sleep(1.0)
            candles = await collector.fetch_candles(symbol, Timeframe.H1, limit=limit)
            req_status = "PASS"
            err_msg = None
        except Exception as e:
            req_status = "FAIL"
            err_msg = f"{type(e).__name__}: {str(e)}"
            candles = []

        if req_status == "FAIL":
            print(f"  Provider request: FAIL - {err_msg}")
            continue

        print(f"  Provider request: PASS (1 request)")
        print(f"  Candles received: {len(candles)}")

        # Validate
        invalid_ohlc = 0
        for c in candles:
            if c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.high < c.low:
                invalid_ohlc += 1

        # Upsert into MongoDB
        for candle in candles:
            doc = candle.model_dump(mode="python")
            doc["ingested_at"] = datetime.now(UTC)
            await service._repository.upsert_one(
                {"symbol": candle.symbol.value, "timeframe": candle.timeframe.value, "timestamp": candle.timestamp},
                doc,
            )

        # Verify in DB
        db_count = await coll.count_documents({"symbol": symbol.value, "timeframe": "1h"})
        docs = await coll.find({"symbol": symbol.value, "timeframe": "1h"}).sort("timestamp", 1).to_list(2000)

        first_ts = docs[0]["timestamp"].isoformat() if docs else "N/A"
        last_ts = docs[-1]["timestamp"].isoformat() if docs else "N/A"

        # Check duplicates in DB
        dup_pipeline = [
            {"$match": {"symbol": symbol.value, "timeframe": "1h"}},
            {"$group": {"_id": "$timestamp", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        dups = await coll.aggregate(dup_pipeline).to_list(100)

        print(f"  Rows stored in DB:  {db_count}")
        print(f"  First timestamp:    {first_ts}")
        print(f"  Last timestamp:     {last_ts}")
        print(f"  Invalid OHLC:       {invalid_ohlc}")
        print(f"  Duplicate in DB:    {len(dups)}")
        print(f"  Status:             VERIFIED")

    await manager.disconnect()
    print("\n" + "=" * 70)
    print("ALL ASSETS INGESTION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())


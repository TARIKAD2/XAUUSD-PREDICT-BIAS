"""Ingest real economic observations from FRED, BLS, and BEA.

Forecast consensus is not supplied by these providers; events are stored with
forecast=null and status=unavailable. The script is idempotent.
"""
import asyncio
import sys

sys.path.insert(0, "backend")

from app.collectors.economic import BeaCollector, BlsCollector, EconomicNormalizationError, FredCollector
from app.core.config import get_settings
from app.db.client import MongoClientManager
from app.services.economic import EconomicService


async def _safe_fetch(name, collector):
    try:
        events = await collector.fetch() if not hasattr(collector, "fetch") else await collector.fetch()
        print(f"[INFO] {name}: fetched {len(events)} observations.")
        return events
    except EconomicNormalizationError as exc:
        print(f"[WARN] {name} unavailable: {exc}")
        return []
    except Exception as exc:
        print(f"[WARN] {name} failed: {type(exc).__name__}")
        return []


async def main():
    settings = get_settings()
    manager = MongoClientManager(settings)
    if not await manager.connect():
        print("[ERROR] Could not connect to MongoDB.")
        return
    service = EconomicService(manager)
    collectors = [
        ("FRED", FredCollector(settings)),
        ("BLS", BlsCollector(settings)),
        ("BEA", BeaCollector(settings)),
    ]
    total = 0
    for name, collector in collectors:
        try:
            events = await collector.fetch() if name != "FRED" else await collector.fetch(limit=10)
        except Exception as exc:
            print(f"[WARN] {name} unavailable: {type(exc).__name__}: {exc}")
            continue
        saved = await service.save_events(events)
        total += saved
        print(f"[INFO] {name}: saved {saved} events.")
    print(f"[INFO] Total saved: {total}")
    await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

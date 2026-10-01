"""Ingest real news items using MarketAux (primary) and RSS fallback, then store them in MongoDB.
The script is safe to run multiple times; upserts are performed based on the URL field.
"""
import asyncio
import sys

# Ensure backend package is on path
sys.path.insert(0, "backend")

from app.core.config import get_settings
from app.db.client import MongoClientManager
from app.services.news import NewsService
from app.collectors.news import MarketAuxCollector, RssCollector

async def main():
    settings = get_settings()
    manager = MongoClientManager(settings)
    if not await manager.connect():
        print("[ERROR] Could not connect to MongoDB.")
        return
    news_service = NewsService(manager)
    # Use MarketAux collector (primary source)
    try:
        aux_collector = MarketAuxCollector(settings)
        items = await aux_collector.fetch(limit=20)
        source_used = "MarketAux"
    except Exception as e:
        print(f"[WARN] MarketAux failed ({e}), falling back to RSS.")
        # Example RSS feed list (common financial news sources)
        rss_urls = [
            "https://www.marketwatch.com/rss/topstories",
            "https://www.reuters.com/tools/rss",
        ]
        rss_collector = RssCollector()
        items = []
        for url in rss_urls:
            try:
                items.extend(await rss_collector.fetch(url, source=url))
            except Exception as rss_e:
                print(f"[WARN] RSS fetch failed for {url}: {rss_e}")
        source_used = "RSS"
    if not items:
        print("[INFO] No news items fetched.")
        await manager.disconnect()
        return
    saved = await news_service.save(items)
    print(f"[INFO] Saved {saved} news items using {source_used} source.")
    await manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())


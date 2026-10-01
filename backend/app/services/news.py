"""Read and persistence service for normalized news."""
from datetime import UTC, datetime

from app.collectors.news import asset_relevance, canonicalize_url
from app.db.client import MongoClientManager
from app.db.collections import NEWS
from app.db.repositories import MongoRepository
from app.schemas.market import AssetSymbol
from app.schemas.news import NewsItem, NewsListResponse


class NewsUnavailableError(RuntimeError):
    pass


def item_matches_symbol(item: NewsItem, symbol: AssetSymbol) -> bool:
    if symbol in item.symbols or item.relevance.get(symbol.value, 0) > 0:
        return True
    # Existing database records created before relevance was persisted are
    # re-evaluated from their published text, never supplemented with fake news.
    return symbol.value in asset_relevance(f"{item.title} {item.description or ''}")


class NewsService:
    def __init__(self, manager: MongoClientManager):
        self._repository = MongoRepository(manager, NEWS)
        self._manager = manager

    async def save(self, items: list[NewsItem]) -> int:
        if not self._manager.is_connected:
            raise NewsUnavailableError("News storage is unavailable.")
        for item in items:
            canonical_url = canonicalize_url(str(item.canonical_url or item.url))
            document = item.model_dump(mode="python")
            document["url"] = canonical_url
            document["canonical_url"] = canonical_url
            document["symbols"] = [symbol.value for symbol in item.symbols]
            document["retrieved_at_utc"] = item.retrieved_at_utc or datetime.now(UTC)
            document["ingested_at"] = datetime.now(UTC)
            await self._repository.upsert_one({"url": canonical_url}, document)
        return len(items)

    async def list(self, limit: int, symbol: AssetSymbol | None = None) -> NewsListResponse:
        if not self._manager.is_connected:
            raise NewsUnavailableError("News storage is unavailable.")
        documents = await self._repository.find_recent({}, max(limit * 5, limit), sort_field="published_at")
        items = [NewsItem.model_validate(document) for document in documents]
        if symbol is not None:
            items = [item for item in items if item_matches_symbol(item, symbol)]
        # Empty results are a valid state; absence of relevant articles is not a
        # storage outage and must remain distinguishable from a 503.
        return NewsListResponse(items=items[:limit], generated_at=datetime.now(UTC))
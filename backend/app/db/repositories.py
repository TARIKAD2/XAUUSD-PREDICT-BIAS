"""Small reusable repository primitives for future collector and ML services."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pymongo import DESCENDING

from .client import MongoClientManager


class MongoRepository:
    """Provide explicit collection access and safe generic persistence operations."""

    def __init__(self, manager: MongoClientManager, collection_name: str) -> None:
        self._manager = manager
        self._collection_name = collection_name

    @property
    def collection(self) -> Any:
        return self._manager.database[self._collection_name]

    async def upsert_one(
        self, identity: Mapping[str, Any], document: Mapping[str, Any]
    ) -> None:
        """Persist one normalized document using its stable identity fields."""
        await self.collection.update_one(
            dict(identity),
            {"$set": dict(document)},
            upsert=True,
        )

    async def find_recent(
        self, filters: Mapping[str, Any], limit: int = 100
    ) -> Sequence[Mapping[str, Any]]:
        """Return a bounded newest-first result set for timestamped collections."""
        cursor = self.collection.find(dict(filters)).sort("timestamp", DESCENDING).limit(limit)
        return await cursor.to_list(length=limit)
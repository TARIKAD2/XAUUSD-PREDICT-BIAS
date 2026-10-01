"""Asynchronous MongoDB client lifecycle and connection-state management."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.database import DatabaseConnectionStatus

from .indexes import ensure_indexes


logger = get_logger(__name__)


class DatabaseNotConnectedError(RuntimeError):
    """Raised when a repository is used before a verified database connection exists."""


class MongoClientManager:
    """Own one async MongoDB client for the FastAPI process lifecycle."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None
        self._database: Any | None = None
        self._status = DatabaseConnectionStatus.NOT_CONFIGURED

    @property
    def status(self) -> DatabaseConnectionStatus:
        return self._status

    @property
    def settings(self) -> Settings:
        """Expose validated non-secret settings to application services."""
        return self._settings

    @property
    def is_connected(self) -> bool:
        return self._status == DatabaseConnectionStatus.CONNECTED and self._database is not None

    @property
    def database(self) -> Any:
        if not self.is_connected:
            raise DatabaseNotConnectedError("MongoDB is not connected.")
        return self._database

    async def connect(self) -> bool:
        """Ping MongoDB and install indexes without leaking connection details on failure."""
        uri = self._settings.mongodb_uri_value
        if uri is None:
            self._status = DatabaseConnectionStatus.NOT_CONFIGURED
            logger.warning(
                "mongodb_not_configured",
                extra={"database_status": self._status.value},
            )
            return False

        await self._close_client()
        self._client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=self._settings.mongodb_server_selection_timeout_ms,
            connectTimeoutMS=self._settings.mongodb_server_selection_timeout_ms,
            server_api=ServerApi(version="1", strict=True, deprecation_errors=True),
            tz_aware=True,
            tzinfo=UTC,
        )
        try:
            await self._client.admin.command("ping")
            self._database = self._client[self._settings.database_name]
            await ensure_indexes(self._database)
        except PyMongoError as exception:
            self._status = DatabaseConnectionStatus.UNAVAILABLE
            logger.error(
                "mongodb_connection_failed",
                extra={
                    "database_status": self._status.value,
                    "error_type": type(exception).__name__,
                },
            )
            await self._close_client()
            self._status = DatabaseConnectionStatus.UNAVAILABLE
            return False

        self._status = DatabaseConnectionStatus.CONNECTED
        logger.info(
            "mongodb_connected",
            extra={"database_status": self._status.value},
        )
        return True

    async def disconnect(self) -> None:
        """Close the process-scoped client when the application stops."""
        await self._close_client()
        logger.info("mongodb_disconnected")

    async def _close_client(self) -> None:
        client, self._client = self._client, None
        self._database = None
        if client is not None:
            result = client.close()
            if hasattr(result, "__await__"):
                await result
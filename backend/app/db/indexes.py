"""Idempotent MongoDB indexes aligned with planned query and deduplication patterns."""

from __future__ import annotations

from typing import Any

from pymongo import ASCENDING, DESCENDING, IndexModel

from .collections import (
    DATA_QUALITY,
    DATASETS,
    ECONOMIC_EVENTS,
    FEATURES,
    MARKET_DATA,
    MODEL_REGISTRY,
    INGESTION_STATE,
    MODEL_METRICS,
    MODEL_PERFORMANCE,
    NEWS,
    PREDICTIONS,
    SYSTEM_LOGS,
    WAR_ROOMS,
)


COLLECTION_INDEXES: dict[str, tuple[IndexModel, ...]] = {
    MARKET_DATA: (
        IndexModel(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("timestamp", ASCENDING)],
            name="market_data_symbol_timeframe_timestamp_unique",
            unique=True,
        ),
    ),
    NEWS: (
        IndexModel([("url", ASCENDING)], name="news_url_unique", unique=True),
        IndexModel([("published_at", DESCENDING)], name="news_published_at_desc"),
    ),
    ECONOMIC_EVENTS: (
        IndexModel(
            [
                ("event", ASCENDING),
                ("country", ASCENDING),
                ("currency", ASCENDING),
                ("timestamp", ASCENDING),
            ],
            name="economic_event_identity_unique",
            unique=True,
        ),
        IndexModel(
            [("timestamp", DESCENDING), ("importance", ASCENDING)],
            name="economic_events_timestamp_importance",
        ),
    ),
    FEATURES: (
        IndexModel(
            [
                ("symbol", ASCENDING),
                ("timeframe", ASCENDING),
                ("timestamp", ASCENDING),
                ("feature_version", ASCENDING),
            ],
            name="features_identity_unique",
            unique=True,
        ),
    ),
    PREDICTIONS: (
        IndexModel(
            [("symbol", ASCENDING), ("timestamp", DESCENDING)],
            name="predictions_symbol_timestamp_desc",
        ),
        IndexModel(
            [("symbol", ASCENDING), ("model_version", ASCENDING), ("timestamp", ASCENDING)],
            name="predictions_identity_unique",
            unique=True,
        ),
    ),
    MODEL_METRICS: (
        IndexModel(
            [
                ("symbol", ASCENDING),
                ("model_version", ASCENDING),
                ("testing_period_end", ASCENDING),
            ],
            name="model_metrics_identity_unique",
            unique=True,
        ),
    ),
    MODEL_PERFORMANCE: (
        IndexModel(
            [
                ("symbol", ASCENDING),
                ("model", ASCENDING),
                ("model_version", ASCENDING),
                ("testing_period_end", ASCENDING),
            ],
            name="model_performance_identity_unique",
            unique=True,
        ),
    ),
    MODEL_REGISTRY: (
        IndexModel(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("status", ASCENDING)],
            name="model_registry_active_lookup",
        ),
        IndexModel(
            [("artifact_sha256", ASCENDING)],
            name="model_registry_artifact_sha256_unique",
            unique=True,
        ),
    ),
    INGESTION_STATE: (
        IndexModel(
            [("symbol", ASCENDING), ("timeframe", ASCENDING)],
            name="ingestion_state_symbol_timeframe_unique",
            unique=True,
        ),
    ),
    DATA_QUALITY: (
        IndexModel(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("generated_at", DESCENDING)],
            name="data_quality_symbol_timeframe_generated",
        ),
    ),
    DATASETS: (
        IndexModel(
            [("symbol", ASCENDING), ("timeframe", ASCENDING), ("created_at", DESCENDING)],
            name="datasets_symbol_timeframe_created",
        ),
    ),
    SYSTEM_LOGS: (
        IndexModel(
            [("timestamp", ASCENDING)],
            name="system_logs_ttl_90_days",
            expireAfterSeconds=60 * 60 * 24 * 90,
        ),
    ),
    WAR_ROOMS: (
        IndexModel([("event_id", ASCENDING)], name="war_rooms_event_id_unique", unique=True),
        IndexModel([("timestamp", DESCENDING)], name="war_rooms_timestamp_desc"),
    ),
}


async def ensure_indexes(database: Any) -> dict[str, list[str]]:
    """Create all application indexes; repeated calls are safe and idempotent."""
    created_indexes: dict[str, list[str]] = {}
    for collection_name, indexes in COLLECTION_INDEXES.items():
        created_indexes[collection_name] = await database[collection_name].create_indexes(list(indexes))
    return created_indexes
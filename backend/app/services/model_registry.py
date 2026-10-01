"""Durable, checksum-verified registry for production model artifacts."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
from pymongo import DESCENDING

from app.db.client import MongoClientManager
from app.db.collections import MODEL_PERFORMANCE, MODEL_REGISTRY
from app.db.repositories import MongoRepository
from app.models.database import ModelRegistryStatus
from app.schemas.market import AssetSymbol, Timeframe


class ModelArtifactError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ModelRegistryService:
    def __init__(self, manager: MongoClientManager):
        self.manager = manager
        self.repository = MongoRepository(manager, MODEL_REGISTRY)
        self.performance_repository = MongoRepository(manager, MODEL_PERFORMANCE)

    async def register_production(self, result: dict[str, Any]) -> dict[str, Any]:
        if not self.manager.is_connected:
            raise ModelArtifactError("Model registry storage is unavailable.")
        metadata = result.get("metadata") or {}
        artifact_value = result.get("path")
        if not artifact_value or not metadata.get("final_test_metrics"):
            raise ModelArtifactError("Only an artifact with real final-test metrics can be promoted.")
        artifact = Path(artifact_value).resolve()
        if not artifact.is_file():
            raise ModelArtifactError("Model artifact is missing.")
        checksum = sha256_file(artifact)
        now = datetime.now(UTC)
        symbol = str(metadata["symbol"])
        timeframe = str(metadata["timeframe"])
        await self.repository.collection.update_many(
            {"symbol": symbol, "timeframe": timeframe, "status": ModelRegistryStatus.PRODUCTION.value},
            {"$set": {"status": ModelRegistryStatus.RETIRED.value, "retired_at": now}},
        )
        document = {
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": metadata["model"],
            "model_version": metadata["model_version"],
            "artifact_path": str(artifact),
            "artifact_sha256": checksum,
            "feature_schema_version": metadata["feature_schema_version"],
            "feature_schema": metadata["feature_manifest"],
            "feature_names": metadata["features"],
            "dataset_version": metadata["dataset_version"],
            "metrics": metadata["final_test_metrics"],
            "validation_metrics": metadata["validation_metrics"],
            "calibration_metrics": metadata["calibration_metrics"],
            "status": ModelRegistryStatus.PRODUCTION.value,
            "created_at": now,
            "promoted_at": now,
        }
        await self.repository.upsert_one({"artifact_sha256": checksum}, document)
        await self.performance_repository.upsert_one(
            {"symbol": symbol, "model": metadata["model"], "model_version": metadata["model_version"], "testing_period_end": metadata["test_end"]},
            {
                "symbol": symbol,
                "model": metadata["model"],
                "model_version": metadata["model_version"],
                "dataset_version": metadata["dataset_version"],
                "feature_version": metadata["feature_schema_version"],
                "training_period_start": metadata["training_start"],
                "training_period_end": metadata["training_end"],
                "testing_period_start": metadata["test_start"],
                "testing_period_end": metadata["test_end"],
                "metrics": [{"name": key, "value": float(value)} for key, value in metadata["final_test_metrics"].items() if isinstance(value, (int, float)) and value is not None],
                "validation_metrics": metadata["validation_metrics"],
                "calibration_metrics": metadata["calibration_metrics"],
                "created_at": now,
            },
        )
        return document

    async def load_production(self, symbol: AssetSymbol, timeframe: Timeframe = Timeframe.H1) -> tuple[dict[str, Any], dict[str, Any]]:
        if not self.manager.is_connected:
            raise ModelArtifactError("Model registry storage is unavailable.")
        registry = await self.repository.collection.find_one(
            {"symbol": symbol.value, "timeframe": timeframe.value, "status": ModelRegistryStatus.PRODUCTION.value},
            sort=[("promoted_at", DESCENDING)],
        )
        if not registry:
            raise ModelArtifactError(f"MODEL_NOT_READY: no promoted model is registered for {symbol.value}.")
        registry.pop("_id", None)
        artifact = Path(registry["artifact_path"])
        if not artifact.is_file():
            raise ModelArtifactError("MODEL_NOT_READY: registered model artifact is missing.")
        if sha256_file(artifact) != registry.get("artifact_sha256"):
            raise ModelArtifactError("ERROR: registered model artifact checksum mismatch.")
        try:
            payload = joblib.load(artifact)
        except Exception as exc:
            raise ModelArtifactError("ERROR: registered model artifact cannot be loaded.") from exc
        metadata = payload.get("metadata") if isinstance(payload, dict) else None
        if not isinstance(metadata, dict) or metadata.get("model_version") != registry.get("model_version"):
            raise ModelArtifactError("ERROR: registered model metadata mismatch.")
        if metadata.get("feature_schema_version") != registry.get("feature_schema_version"):
            raise ModelArtifactError("ERROR: registered feature schema mismatch.")
        if payload.get("model") is None or payload.get("label_encoder") is None:
            raise ModelArtifactError("ERROR: registered inference package is incomplete.")
        return registry, payload
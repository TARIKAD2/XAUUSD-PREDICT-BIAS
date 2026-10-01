"""Model-performance status service; never invents evaluation records."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.db.collections import MODEL_PERFORMANCE
from app.db.repositories import MongoRepository
from app.core.config import get_settings
from app.schemas.market import AssetSymbol
from app.schemas.performance import ModelMetric, ModelPerformance, ModelPerformanceResponse


class ModelPerformanceUnavailableError(RuntimeError):
    pass


def _parse_dt(value) -> datetime:
    parsed = pd.to_datetime(value, utc=True)
    if pd.isna(parsed):
        raise ValueError("missing timestamp")
    return parsed.to_pydatetime()


def _row_to_performance(row: dict) -> ModelPerformance | None:
    try:
        symbol = AssetSymbol(str(row.get("symbol")))
        metrics = []
        for name in ("accuracy", "precision", "recall", "f1", "log_loss", "brier"):
            if name in row and row[name] is not None and str(row[name]) != "":
                metrics.append(ModelMetric(name=name, value=float(row[name])))
        if isinstance(row.get("metrics"), list):
            metrics = [ModelMetric(name=str(m["name"]), value=float(m["value"])) for m in row["metrics"]]
        return ModelPerformance(
            symbol=symbol,
            model_version=str(row.get("model_version") or row.get("model") or "unknown"),
            training_period_start=_parse_dt(row.get("training_period_start") or row.get("timestamp")),
            training_period_end=_parse_dt(row.get("training_period_end") or row.get("timestamp")),
            testing_period_start=_parse_dt(row.get("testing_period_start") or row.get("timestamp")),
            testing_period_end=_parse_dt(row.get("testing_period_end") or row.get("timestamp")),
            feature_version=str(row.get("feature_version") or "1.0"),
            metrics=metrics,
        )
    except Exception:
        return None


class ModelPerformanceService:
    def __init__(self, manager):
        self.manager = manager
        self.models_dir = get_settings().models_dir

    async def list(self) -> ModelPerformanceResponse:
        if not self.manager.is_connected:
            raise ModelPerformanceUnavailableError("NO_DATA: model-metric storage is unavailable.")
        items: list[ModelPerformance] = []
        try:
            repo = MongoRepository(self.manager, MODEL_PERFORMANCE)
            docs = await repo.find_recent({}, limit=100)
            for doc in docs:
                parsed = _row_to_performance(doc)
                if parsed:
                    items.append(parsed)
        except Exception:
            pass

        perf_path = Path(self.models_dir) / "performance_history.csv"
        if perf_path.exists():
            try:
                df = pd.read_csv(perf_path)
                for row in df.to_dict(orient="records"):
                    parsed = _row_to_performance(row)
                    if parsed:
                        items.append(parsed)
            except Exception as exc:
                if not items:
                    raise ModelPerformanceUnavailableError("ERROR: could not read performance history.") from exc

        if not items:
            raise ModelPerformanceUnavailableError(
                "MODEL_NOT_READY: no persisted out-of-sample model metrics are registered."
            )
        return ModelPerformanceResponse(items=items, generated_at=datetime.now(UTC))

    def get_latest(self) -> dict:
        out_dir = Path(self.models_dir)
        if not out_dir.exists():
            raise ModelPerformanceUnavailableError(
                "MODEL_NOT_READY: no persisted out-of-sample model metrics are registered."
            )
        json_files = list(out_dir.glob("*.json"))
        if not json_files:
            raise ModelPerformanceUnavailableError("MODEL_NOT_READY: no JSON performance artifacts found.")
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, encoding="utf-8") as handle:
            return json.load(handle)

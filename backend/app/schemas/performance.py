"""Schemas for historical model-quality reporting."""

from datetime import datetime

from pydantic import Field

from .base import APIModel
from .market import AssetSymbol


class ModelMetric(APIModel):
    name: str
    value: float = Field(ge=0)


class ModelPerformance(APIModel):
    symbol: AssetSymbol
    model_version: str
    training_period_start: datetime
    training_period_end: datetime
    testing_period_start: datetime
    testing_period_end: datetime
    feature_version: str
    metrics: list[ModelMetric]


class ModelPerformanceResponse(APIModel):
    items: list[ModelPerformance]
    generated_at: datetime
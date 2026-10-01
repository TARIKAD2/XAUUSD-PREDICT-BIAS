"""Schemas for probabilistic and explainable model predictions."""

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from .base import APIModel
from .market import AssetSymbol


class MarketDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class ProbabilityBreakdown(APIModel):
    bullish: float = Field(ge=0, le=1)
    bearish: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def probabilities_sum_to_one(self) -> "ProbabilityBreakdown":
        if abs(self.bullish + self.bearish - 1.0) > 0.001:
            raise ValueError("Prediction probabilities must sum to 1")
        return self


class FeatureContribution(APIModel):
    feature: str
    contribution: float
    value: float | None = None
    direction: str | None = None
    rank: int | None = Field(default=None, ge=1)


class Scenario(APIModel):
    name: str
    condition: str
    expected_direction: MarketDirection
    invalidation: str
    context: str


class PredictionResponse(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    direction: MarketDirection
    probabilities: ProbabilityBreakdown
    confidence: float = Field(ge=0, le=1)
    model: str
    model_version: str
    top_features: list[FeatureContribution] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    invalidation: list[str] = Field(default_factory=list)
    data_quality: str = "UNKNOWN"
    market_context: str | None = None
    data_timestamp: datetime | None = None
    scenarios: list[Scenario] = Field(default_factory=list)
    feature_schema_version: str = "unknown"
    prediction_timestamp_utc: datetime | None = None
    prediction_as_of: datetime | None = None
    market_as_of_utc: datetime | None = None
    quality_reasons: list[str] = Field(default_factory=list)
    explanation_method: str = "unavailable"
    horizon: str = "24h"
    horizon_hours: int = 24


class PredictionListResponse(APIModel):
    items: list[PredictionResponse]
    generated_at: datetime

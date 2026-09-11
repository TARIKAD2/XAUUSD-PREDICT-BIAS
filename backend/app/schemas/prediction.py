"""Schemas for probabilistic and explainable model predictions."""

from datetime import datetime
from enum import Enum

from pydantic import Field, model_validator

from .base import APIModel
from .market import AssetSymbol


class MarketDirection(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class ProbabilityBreakdown(APIModel):
    bullish: float = Field(ge=0, le=1)
    neutral: float = Field(ge=0, le=1)
    bearish: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def probabilities_sum_to_one(self) -> "ProbabilityBreakdown":
        if abs(self.bullish + self.neutral + self.bearish - 1.0) > 0.001:
            raise ValueError("Prediction probabilities must sum to 1")
        return self


class PredictionResponse(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    direction: MarketDirection
    probabilities: ProbabilityBreakdown
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    invalidation: list[str]
    model_version: str


class PredictionListResponse(APIModel):
    items: list[PredictionResponse]
    generated_at: datetime
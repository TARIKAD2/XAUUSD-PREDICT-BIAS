"""Schemas for model explanations derived from actual SHAP values."""
from datetime import datetime

from .base import APIModel
from .market import AssetSymbol
from .prediction import FeatureContribution


class ExplanationResponse(APIModel):
    symbol: AssetSymbol
    timestamp: datetime
    model: str
    model_version: str
    method: str
    top_features: list[FeatureContribution]
    available: bool
    note: str
    feature_schema_version: str = "unknown"
    explanation_as_of: datetime | None = None
    market_as_of_utc: datetime | None = None

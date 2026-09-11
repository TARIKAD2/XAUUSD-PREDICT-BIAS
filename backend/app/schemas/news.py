"""Schemas for normalized financial-news records."""

from datetime import datetime
from enum import Enum

from pydantic import AnyHttpUrl

from .base import APIModel
from .market import AssetSymbol


class NewsSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class NewsImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NewsItem(APIModel):
    title: str
    description: str | None = None
    source: str
    url: AnyHttpUrl
    published_at: datetime
    symbols: list[AssetSymbol] = []
    currencies: list[str] = []
    countries: list[str] = []
    sentiment: NewsSentiment
    importance: NewsImportance


class NewsListResponse(APIModel):
    items: list[NewsItem]
    generated_at: datetime
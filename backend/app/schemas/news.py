"""Schemas for normalized financial-news records."""
from datetime import datetime
from enum import Enum
from pydantic import AnyHttpUrl, Field
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


class NewsCategory(str, Enum):
    MACRO = "macro"
    MONETARY_POLICY = "monetary_policy"
    GEOPOLITICS = "geopolitics"
    MARKET = "market"
    COMMODITIES = "commodities"
    OTHER = "other"


class SentimentSource(str, Enum):
    PROVIDER = "provider"
    LEXICON = "lexicon"


class MarketImpact(APIModel):
    asset: AssetSymbol
    direction: NewsSentiment
    rationale: str


class NewsItem(APIModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    source: str = Field(min_length=1, max_length=120)
    url: AnyHttpUrl
    published_at: datetime
    symbols: list[AssetSymbol] = Field(default_factory=list)
    currencies: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    category: NewsCategory
    sentiment: NewsSentiment
    sentiment_source: SentimentSource = SentimentSource.LEXICON
    importance: NewsImportance
    impacts: list[MarketImpact] = Field(default_factory=list)
    provider: str | None = None
    canonical_url: AnyHttpUrl | None = None
    retrieved_at_utc: datetime | None = None
    relevance: dict[str, float] = Field(default_factory=dict)


class NewsListResponse(APIModel):
    items: list[NewsItem]
    generated_at: datetime

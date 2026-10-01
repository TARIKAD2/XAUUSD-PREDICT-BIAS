"""RSS and MarketAux news collection with explicit asset relevance."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx

from app.core.config import Settings
from app.schemas.market import AssetSymbol
from app.schemas.news import (
    MarketImpact,
    NewsCategory,
    NewsImportance,
    NewsItem,
    NewsSentiment,
    SentimentSource,
)

POSITIVE = {"rally", "rallies", "gain", "gains", "eases", "easing", "dovish", "beat", "beats"}
NEGATIVE = {"loss", "losses", "decline", "declines", "hawkish", "miss", "misses", "recession", "war"}
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}
ASSET_TERMS = {
    AssetSymbol.XAUUSD: ("xauusd", "xau/usd", "gold", "gold price", "bullion", "precious metal", "precious metals"),
}


class NewsCollectionError(RuntimeError):
    pass


def canonicalize_url(value: str) -> str:
    """Remove fragment and common tracking parameters before deduplication."""
    parsed = urlsplit(value.strip())
    query = urlencode(sorted((key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True) if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS))
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, query, ""))


def asset_relevance(text: str) -> dict[str, float]:
    normalized = re.sub(r"\s+", " ", text.lower())
    return {
        symbol.value: 1.0
        for symbol, terms in ASSET_TERMS.items()
        if any(term in normalized for term in terms)
    }


def classify(text: str):
    tokens = set(re.findall(r"[a-z]+", text.lower()))
    score = len(tokens & POSITIVE) - len(tokens & NEGATIVE)
    sentiment = NewsSentiment.POSITIVE if score > 0 else NewsSentiment.NEGATIVE if score < 0 else NewsSentiment.NEUTRAL
    relevance = asset_relevance(text)
    symbols = [AssetSymbol(symbol) for symbol in relevance]
    category = (
        NewsCategory.MONETARY_POLICY
        if tokens & {"fed", "ecb", "boj", "boe", "fomc", "rate"}
        else NewsCategory.MACRO
        if tokens & {"cpi", "gdp", "employment", "nfp", "pce"}
        else NewsCategory.COMMODITIES
        if AssetSymbol.XAUUSD.value in relevance
        else NewsCategory.GEOPOLITICS
        if tokens & {"war", "sanction"}
        else NewsCategory.MARKET
    )
    importance = NewsImportance.HIGH if category in {NewsCategory.MACRO, NewsCategory.MONETARY_POLICY} else NewsImportance.MEDIUM if symbols else NewsImportance.LOW
    impacts = [
        MarketImpact(asset=symbol, direction=sentiment, rationale="Published-text relevance and sentiment classification.")
        for symbol in symbols
    ]
    return sentiment, category, importance, symbols, impacts, relevance


def _parse_published(raw: object) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        if isinstance(raw, datetime):
            parsed = raw
        else:
            try:
                parsed = parsedate_to_datetime(str(raw))
            except (TypeError, ValueError):
                parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except (TypeError, ValueError):
        return None


def _sentiment_from_score(score: float) -> NewsSentiment:
    if score > 0.05:
        return NewsSentiment.POSITIVE
    if score < -0.05:
        return NewsSentiment.NEGATIVE
    return NewsSentiment.NEUTRAL


def normalize_rss(xml: bytes, source: str, retrieved_at: datetime | None = None) -> list[NewsItem]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise NewsCollectionError("RSS feed is malformed.") from exc
    fetched_at = retrieved_at or datetime.now(UTC)
    out: list[NewsItem] = []
    for entry in root.findall(".//item"):
        title = (entry.findtext("title") or "").strip()
        raw_url = (entry.findtext("link") or "").strip()
        if not title or not raw_url:
            continue
        url = canonicalize_url(raw_url)
        description = (entry.findtext("description") or "").strip() or None
        published = _parse_published(entry.findtext("pubDate"))
        if published is None:
            continue
        sentiment, category, importance, symbols, impacts, relevance = classify(f"{title} {description or ''}")
        out.append(NewsItem(
            title=title[:500], description=description, source=source, provider="rss", url=url,
            canonical_url=url, published_at=published, retrieved_at_utc=fetched_at,
            symbols=symbols, category=category, sentiment=sentiment,
            sentiment_source=SentimentSource.LEXICON, importance=importance, impacts=impacts, relevance=relevance,
        ))
    return out


class RssCollector:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    async def fetch(self, url: str, source: str) -> list[NewsItem]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers={"User-Agent": "AI-Market-Intelligence/0.1 (+research)"})
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise NewsCollectionError("RSS request failed.") from exc
        return normalize_rss(response.content, source, datetime.now(UTC))


class MarketAuxCollector:
    """Collect and normalize financial news from MarketAux."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def fetch(self, limit: int = 10, symbols: list[str] | None = None) -> list[NewsItem]:
        api_key = self._settings.marketaux_api_key or self._settings.news_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise NewsCollectionError("MARKETAUX_API_KEY is not configured.")
        params: dict[str, object] = {"api_token": api_key.get_secret_value(), "limit": limit, "language": "en"}
        if symbols:
            params["symbols"] = ",".join(symbols)
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        retrieved_at = datetime.now(UTC)
        try:
            response = await client.get("https://api.marketaux.com/v1/news/all", params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise NewsCollectionError("MarketAux request failed.") from exc
        finally:
            if owns_client:
                await client.aclose()
        items: list[NewsItem] = []
        for article in payload.get("data", []) if isinstance(payload, dict) else []:
            title = (article.get("title") or "").strip()
            raw_url = (article.get("url") or "").strip()
            if not title or not raw_url:
                continue
            url = canonicalize_url(raw_url)
            description = (article.get("description") or article.get("snippet") or "").strip() or None
            published = _parse_published(article.get("published_at"))
            if published is None:
                continue
            lexicon_sentiment, category, importance, detected_symbols, impacts, relevance = classify(f"{title} {description or ''}")
            scores: list[float] = []
            for entity in article.get("entities") or []:
                if isinstance(entity, dict) and entity.get("sentiment_score") is not None:
                    try:
                        scores.append(float(entity["sentiment_score"]))
                    except (TypeError, ValueError):
                        continue
            sentiment = _sentiment_from_score(sum(scores) / len(scores)) if scores else lexicon_sentiment
            sentiment_source = SentimentSource.PROVIDER if scores else SentimentSource.LEXICON
            try:
                items.append(NewsItem(
                    title=title[:500], description=description, source=str(article.get("source") or "MarketAux")[:120],
                    provider="marketaux", url=url, canonical_url=url, published_at=published, retrieved_at_utc=retrieved_at,
                    symbols=detected_symbols, currencies=["USD"] if detected_symbols else [], countries=["US"],
                    category=category, sentiment=sentiment, sentiment_source=sentiment_source,
                    importance=importance, impacts=impacts, relevance=relevance,
                ))
            except Exception:
                continue
        return items
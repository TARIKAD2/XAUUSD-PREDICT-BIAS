"""Real historical dataset construction with closed-candle and as-of rules."""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.db.collections import MARKET_DATA
from app.features.canonical import FEATURE_SCHEMA_VERSION, build_canonical_features
from app.schemas.market import Timeframe, candle_is_closed


DATASET_VERSION = "1.1"


def fetch_raw_candles(manager: Any, symbol: Any, timeframe: Any) -> pd.DataFrame:
    """Fetch closed candles from the shared ``market_data`` collection for sync callers."""
    symbol_value = getattr(symbol, "value", str(symbol))
    timeframe_value = getattr(timeframe, "value", str(timeframe))
    if manager is None or not getattr(manager, "is_connected", False):
        return pd.DataFrame()
    cursor = manager.database[MARKET_DATA].find({"symbol": symbol_value, "timeframe": timeframe_value})
    if hasattr(cursor, "to_list"):
        raise TypeError("Use fetch_raw_candles_async with Motor; this helper is for sync documents.")
    return _candles_frame(list(cursor), timeframe_value)


async def fetch_raw_candles_async(manager: Any, symbol: Any, timeframe: Any, limit: int = 20000) -> pd.DataFrame:
    """Async read of historical closed candles only."""
    if manager is None or not getattr(manager, "is_connected", False):
        return pd.DataFrame()
    symbol_value = getattr(symbol, "value", str(symbol))
    timeframe_value = getattr(timeframe, "value", str(timeframe))
    cursor = manager.database[MARKET_DATA].find({"symbol": symbol_value, "timeframe": timeframe_value})
    documents = await cursor.to_list(length=limit)
    return _candles_frame(documents, timeframe_value)


def _candles_frame(documents: list[dict], timeframe_value: str) -> pd.DataFrame:
    if not documents:
        return pd.DataFrame()
    frame = pd.DataFrame(documents).drop(columns=["_id", "ingested_at"], errors="ignore")
    if "timestamp" not in frame.columns:
        return pd.DataFrame()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    timeframe = Timeframe(timeframe_value)
    frame = frame.dropna(subset=["timestamp"])
    closed_mask = frame.apply(
        lambda row: row.get("is_closed") is not False and candle_is_closed(row["timestamp"].to_pydatetime(), timeframe),
        axis=1,
    )
    return frame.loc[closed_mask].sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)


def define_target(
    frame: pd.DataFrame,
    horizon_periods: int = 1,
    bullish_threshold: float = 0.001,
    bearish_threshold: float = -0.001,
) -> pd.DataFrame:
    """Label T exclusively from a close strictly after T."""
    if frame.empty or "close" not in frame.columns or "timestamp" not in frame.columns:
        return frame
    out = frame.sort_values("timestamp").copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    out["future_close"] = out["close"].shift(-horizon_periods)
    out["future_timestamp"] = out["timestamp"].shift(-horizon_periods)
    expected_interval = pd.Timedelta(hours=horizon_periods)
    contiguous_horizon = (out["future_timestamp"] - out["timestamp"]) == expected_interval
    horizon_gap_exclusions = int((out["future_timestamp"].notna() & ~contiguous_horizon).sum())
    out["future_return"] = (out["future_close"] / out["close"]) - 1.0

    def categorize(value: float) -> str:
        if pd.isna(value):
            return "UNKNOWN"
        if value >= 0:
            return "BULLISH"
        return "BEARISH"

    out["target"] = out["future_return"].where(contiguous_horizon).apply(categorize)
    out = out.loc[out["target"] != "UNKNOWN"].copy()
    out = out.drop(columns=["future_close", "future_timestamp", "future_return"])
    out.attrs["horizon_gap_exclusion_count"] = horizon_gap_exclusions
    return out


def _asof_events(primary: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Join only events with an explicit known-at timestamp and vintage."""
    if events is None or events.empty:
        return primary
    right = events.copy()
    release_column = "release_time_utc" if "release_time_utc" in right.columns else None
    if release_column is None:
        return primary
    right["available_at"] = pd.to_datetime(right[release_column], utc=True, errors="coerce")
    if "vintage_time_utc" in right.columns:
        vintage = pd.to_datetime(right["vintage_time_utc"], utc=True, errors="coerce")
        right["available_at"] = right[["available_at"]].join(vintage.rename("vintage")).max(axis=1)
    right = right.dropna(subset=["available_at"])
    if right.empty:
        return primary
    keep = [column for column in ("available_at", "actual", "surprise") if column in right.columns]
    right = right[keep].rename(columns={"available_at": "timestamp", "actual": "econ_actual", "surprise": "econ_surprise"})
    return pd.merge_asof(primary.sort_values("timestamp"), right.sort_values("timestamp"), on="timestamp", direction="backward")


def _asof_news(primary: pd.DataFrame, news: pd.DataFrame) -> pd.DataFrame:
    if news is None or news.empty or "published_at" not in news.columns:
        return primary
    right = news.copy()
    right["timestamp"] = pd.to_datetime(right["published_at"], utc=True, errors="coerce")
    right = right.dropna(subset=["timestamp"])
    sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
    right["news_sentiment_score"] = right.get("sentiment", pd.Series(index=right.index, dtype=str)).map(
        lambda value: sentiment_map.get(str(value).lower(), 0.0)
    )
    right = right[["timestamp", "news_sentiment_score"]].groupby("timestamp", as_index=False).mean()
    return pd.merge_asof(primary.sort_values("timestamp"), right.sort_values("timestamp"), on="timestamp", direction="backward")


def build_training_dataset(
    raw_ohlc: pd.DataFrame,
    horizon_periods: int = 1,
    bullish_threshold: float = 0.001,
    bearish_threshold: float = -0.001,
    related_markets: dict[str, pd.DataFrame] | None = None,
    economic_events: pd.DataFrame | None = None,
    news: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Build an as-of, closed-candle training frame from verified inputs."""
    del related_markets  # Cross-market features require an online contract before promotion.
    if raw_ohlc.empty:
        return pd.DataFrame(), {"error": "Empty input"}
    frame = raw_ohlc.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    invalid_mask = (frame["high"] < frame[["open", "close"]].max(axis=1)) | (frame["low"] > frame[["open", "close"]].min(axis=1))
    invalid_ohlc = int(invalid_mask.sum())
    frame = frame.loc[~invalid_mask].copy()
    symbol = str(frame["symbol"].iloc[0]) if "symbol" in frame.columns and not frame.empty else "UNKNOWN"
    featured = build_canonical_features(frame, symbol)
    featured = _asof_events(featured, economic_events if economic_events is not None else pd.DataFrame())
    featured = _asof_news(featured, news if news is not None else pd.DataFrame())
    targeted = define_target(featured, horizon_periods, bullish_threshold, bearish_threshold)
    horizon_gap_exclusions = int(targeted.attrs.get("horizon_gap_exclusion_count", 0))
    unavailable = [column for column in targeted.columns if column != "target" and targeted[column].isna().all()]
    targeted = targeted.drop(columns=unavailable)
    clean = targeted.dropna().copy()
    counts = clean["target"].value_counts().to_dict() if not clean.empty else {}
    quality = {
        "symbol": symbol,
        "dataset_version": DATASET_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "start_timestamp": str(clean["timestamp"].min()) if not clean.empty else None,
        "end_timestamp": str(clean["timestamp"].max()) if not clean.empty else None,
        "number_of_rows": len(raw_ohlc),
        "valid_target_count": len(clean),
        "invalid_ohlc_count": invalid_ohlc,
        "duplicate_count": len(raw_ohlc) - len(raw_ohlc.drop_duplicates(subset=["timestamp"])),
        "horizon_gap_exclusion_count": horizon_gap_exclusions,
        "unavailable_features": unavailable,
        "label_definition": f"future_return_{horizon_periods} >= 0: BULLISH; < 0: BEARISH",
        "class_distribution": {"bullish": int(counts.get("BULLISH", 0)), "bearish": int(counts.get("BEARISH", 0))},
    }
    return clean.reset_index(drop=True), quality
"""Canonical, leakage-safe feature contract shared by training and inference."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.features.structure import add_structure_features
from app.features.technical import build_technical_features


FEATURE_SCHEMA_VERSION = "2.0"
RAW_COLUMNS = {"timestamp", "symbol", "timeframe", "open", "high", "low", "close", "volume", "target"}


def build_canonical_features(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Create features using data available at each candle close only.

    This function is the only feature builder used by both model fitting and
    live inference. It never fills unavailable volume-derived values.
    """
    featured = build_technical_features(frame)
    featured = add_structure_features(featured, symbol)
    featured["body"] = featured["close"] - featured["open"]
    featured["upper_wick"] = featured["high"] - featured[["open", "close"]].max(axis=1)
    featured["lower_wick"] = featured[["open", "close"]].min(axis=1) - featured["low"]
    featured["rolling_high_20"] = featured["high"].rolling(20, min_periods=20).max()
    featured["rolling_low_20"] = featured["low"].rolling(20, min_periods=20).min()
    featured["rolling_high_50"] = featured["high"].rolling(50, min_periods=50).max()
    featured["rolling_low_50"] = featured["low"].rolling(50, min_periods=50).min()
    if "poc" in featured:
        featured["distance_to_poc"] = (featured["close"] / featured["poc"]) - 1.0
    return featured


def feature_names(frame: pd.DataFrame) -> list[str]:
    """Return the deterministic numeric inference contract in column order."""
    return [
        column
        for column in frame.columns
        if column not in RAW_COLUMNS and pd.api.types.is_numeric_dtype(frame[column])
    ]


def feature_manifest(frame: pd.DataFrame, timeframe: str = "1h") -> list[dict[str, Any]]:
    """Describe the exact persisted feature contract without inventing values."""
    return [
        {
            "name": name,
            "dtype": str(frame[name].dtype),
            "source": "market_ohlc" if name not in {"poc", "distance_to_poc"} else "market_volume",
            "timeframe": timeframe,
            "availability": "derived_from_closed_candles",
            "schema_version": FEATURE_SCHEMA_VERSION,
        }
        for name in feature_names(frame)
    ]
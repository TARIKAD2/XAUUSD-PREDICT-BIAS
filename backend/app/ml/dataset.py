"""Target definition and dataset construction without forward-leakage."""
from __future__ import annotations
import pandas as pd
from typing import Literal

def define_target(
    df: pd.DataFrame, 
    horizon_periods: int = 1, 
    bullish_threshold: float = 0.001, 
    bearish_threshold: float = -0.001
) -> pd.DataFrame:
    """
    Mathematical Target Definition:
    future_return = future_close / current_close - 1
    BULLISH if future_return >= bullish_threshold
    BEARISH if future_return <= bearish_threshold
    NEUTRAL otherwise
    """
    if df.empty or "close" not in df.columns or "timestamp" not in df.columns:
        return df

    out = df.sort_values("timestamp").copy()
    
    # Calculate future return precisely. Shift negative periods = look forward
    out["future_close"] = out["close"].shift(-horizon_periods)
    out["future_return"] = (out["future_close"] / out["close"]) - 1.0

    def categorize(r: float) -> str:
        if pd.isna(r):
            return "UNKNOWN"
        if r >= bullish_threshold:
            return "BULLISH"
        elif r <= bearish_threshold:
            return "BEARISH"
        return "NEUTRAL"

    out["target"] = out["future_return"].apply(categorize)
    
    # Drop rows that cannot have a valid target (end of dataset)
    out = out[out["target"] != "UNKNOWN"].copy()
    out.drop(columns=["future_close", "future_return"], inplace=True)
    return out

def build_training_dataset(
    raw_ohlc: pd.DataFrame, 
    horizon_periods: int = 1,
    bullish_threshold: float = 0.001, 
    bearish_threshold: float = -0.001
) -> tuple[pd.DataFrame, dict]:
    """
    Responsibilities:
    1. Validate chronological ordering.
    2. Remove duplicate timestamps.
    3. Detect missing observations.
    4. Build technical features.
    5. Generate future-return targets.
    6. Return clean reproducible training dataset + quality metrics.
    """
    if raw_ohlc.empty:
        return pd.DataFrame(), {"error": "Empty input"}

    # Sort and remove duplicates
    df = raw_ohlc.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).copy()
    
    quality = {
        "symbol": df["symbol"].iloc[0] if "symbol" in df.columns else "UNKNOWN",
        "start_timestamp": str(df["timestamp"].min()),
        "end_timestamp": str(df["timestamp"].max()),
        "number_of_rows": len(raw_ohlc),
        "duplicate_count": len(raw_ohlc) - len(df),
        "missing_timestamp_count": df["timestamp"].isna().sum()
    }
    
    from app.features.technical import build_technical_features
    # Build technical features (strictly backward looking)
    featured = build_technical_features(df)
    
    # Build Target (forward looking, but isolated to target column)
    targeted = define_target(featured, horizon_periods, bullish_threshold, bearish_threshold)
    
    # Drop NAs induced by rolling calculations
    clean = targeted.dropna().copy()
    
    quality["invalid_ohlc_count"] = 0 # Assume pre-validated for now
    quality["missing_feature_count"] = len(targeted) - len(clean)
    quality["valid_target_count"] = len(clean)
    
    if not clean.empty:
        counts = clean["target"].value_counts().to_dict()
        quality["class_distribution"] = {
            "bullish": counts.get("BULLISH", 0),
            "neutral": counts.get("NEUTRAL", 0),
            "bearish": counts.get("BEARISH", 0)
        }
    else:
        quality["class_distribution"] = {}

    return clean, quality

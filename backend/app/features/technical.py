"""Leakage-safe technical and cross-market feature construction."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _session_from_hour(hour: int) -> int:
    if 0 <= hour < 7:
        return 0  # Asia
    if 7 <= hour < 13:
        return 1  # London
    if 13 <= hour < 21:
        return 2  # New York
    return 0


def build_technical_features(frame: pd.DataFrame) -> pd.DataFrame:
    if not {"timestamp", "open", "high", "low", "close"} <= set(frame.columns):
        raise ValueError("Missing OHLC columns.")
    df = frame.sort_values("timestamp").drop_duplicates("timestamp").copy()

    # ── Core returns ────────────────────────────────────────────────────────
    df["return_1"] = df.close.pct_change()
    df["log_return_1"] = np.log(df.close / df.close.shift(1))

    # ── Momentum (multiple horizons) ────────────────────────────────────────
    df["momentum_5"] = df.close.pct_change(5)
    df["momentum_10"] = df.close.pct_change(10)
    df["momentum_20"] = df.close.pct_change(20)

    # ── Moving averages ─────────────────────────────────────────────────────
    df["sma_20"] = df.close.rolling(20, min_periods=20).mean()
    df["sma_50"] = df.close.rolling(50, min_periods=50).mean()
    df["sma_200"] = df.close.rolling(200, min_periods=200).mean()
    df["ema_20"] = df.close.ewm(span=20, adjust=False).mean()
    df["ema_50"] = df.close.ewm(span=50, adjust=False).mean()

    # ── MACD (12/26/9) ──────────────────────────────────────────────────────
    fast = df.close.ewm(span=12, adjust=False).mean()
    slow = df.close.ewm(span=26, adjust=False).mean()
    df["macd"] = fast - slow
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # ── RSI-14 ──────────────────────────────────────────────────────────────
    d = df.close.diff()
    g = d.clip(lower=0).rolling(14, min_periods=14).mean()
    l = (-d.clip(upper=0)).rolling(14, min_periods=14).mean()
    df["rsi_14"] = 100 - 100 / (1 + g / l.replace(0, float("nan")))

    # ── ATR and normalised ATR ───────────────────────────────────────────────
    df["atr_14"] = (df.high - df.low).rolling(14, min_periods=14).mean()
    df["atr_pct"] = df["atr_14"] / df["close"]  # dimensionless volatility proxy

    # ── Bollinger Bands (20-period, 2σ) ─────────────────────────────────────
    bb_std = df.close.rolling(20, min_periods=20).std()
    df["bb_upper"] = df["sma_20"] + 2.0 * bb_std
    df["bb_lower"] = df["sma_20"] - 2.0 * bb_std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["sma_20"].replace(0, float("nan"))

    # ── Price vs moving averages (normalised distance) ──────────────────────
    df["close_vs_sma50"] = (df["close"] / df["sma_50"].replace(0, float("nan"))) - 1.0
    df["close_vs_sma200"] = (df["close"] / df["sma_200"].replace(0, float("nan"))) - 1.0

    # ── Range / candle shape ─────────────────────────────────────────────────
    df["range"] = df.high - df.low
    df["high_low_ratio"] = df["high"] / df["low"].replace(0, float("nan")) - 1.0

    # ── Volatility (multiple horizons) ──────────────────────────────────────
    df["volatility_5"] = df.return_1.rolling(5, min_periods=5).std()
    df["volatility_20"] = df.return_1.rolling(20, min_periods=20).std()
    df["volatility_50"] = df.return_1.rolling(50, min_periods=50).std()

    # ── Calendar / session features ─────────────────────────────────────────
    ts = pd.to_datetime(df["timestamp"], utc=True)
    df["hour_utc"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["session"] = df["hour_utc"].map(_session_from_hour)

    return df


def add_cross_market_features(primary: pd.DataFrame, related: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Backward-only as-of join; a primary row can only receive earlier related data."""
    left = primary.sort_values("timestamp").copy()
    right = related.sort_values("timestamp")[["timestamp", "close"]].rename(columns={"close": f"{prefix}_close"})
    out = pd.merge_asof(left, right, on="timestamp", direction="backward", allow_exact_matches=True)
    out[f"{prefix}_return_1"] = out[f"{prefix}_close"].pct_change()
    return out

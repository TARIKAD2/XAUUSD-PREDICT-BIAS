"""XAUUSD structure features computed only from available OHLC/volume."""
from __future__ import annotations

import numpy as np
import pandas as pd

XAU_SYMBOLS = {"XAUUSD"}


def add_structure_features(frame: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """Add POC/FVG/order-block/structure columns when the series is XAUUSD.

    Missing volume or insufficient history yields NaN (unavailable), never invented prices.
    """
    df = frame.copy()
    symbol_value = symbol or (str(df["symbol"].iloc[0]) if "symbol" in df.columns and not df.empty else "")
    if symbol_value not in XAU_SYMBOLS:
        return df
    if len(df) < 5 or not {"high", "low", "close"} <= set(df.columns):
        df["poc"] = np.nan
        df["bullish_fvg"] = np.nan
        df["bearish_fvg"] = np.nan
        df["order_block"] = np.nan
        df["market_structure"] = np.nan
        return df

    df["poc"] = _rolling_poc(df)
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    bullish_fvg = np.full(len(df), np.nan)
    bearish_fvg = np.full(len(df), np.nan)
    for i in range(2, len(df)):
        if low[i] > high[i - 2]:
            bullish_fvg[i] = 1.0
            bearish_fvg[i] = 0.0
        elif high[i] < low[i - 2]:
            bearish_fvg[i] = 1.0
            bullish_fvg[i] = 0.0
        else:
            bullish_fvg[i] = 0.0
            bearish_fvg[i] = 0.0
    df["bullish_fvg"] = bullish_fvg
    df["bearish_fvg"] = bearish_fvg
    df["order_block"] = _order_block(close)
    df["market_structure"] = _market_structure(high, low)
    return df


def _rolling_poc(df: pd.DataFrame, window: int = 50) -> pd.Series:
    if "volume" not in df.columns or df["volume"].fillna(0).sum() <= 0:
        return pd.Series(np.nan, index=df.index)
    values = []
    closes = df["close"].to_numpy()
    volumes = df["volume"].fillna(0).to_numpy()
    for i in range(len(df)):
        start = max(0, i - window + 1)
        if i - start + 1 < 10 or volumes[start : i + 1].sum() <= 0:
            values.append(np.nan)
            continue
        prices = closes[start : i + 1]
        vols = volumes[start : i + 1]
        bins = min(20, len(prices))
        hist, edges = np.histogram(prices, bins=bins, weights=vols)
        poc = float((edges[int(np.argmax(hist))] + edges[int(np.argmax(hist)) + 1]) / 2)
        values.append(poc)
    return pd.Series(values, index=df.index)


def _order_block(close: np.ndarray) -> np.ndarray:
    out = np.full(len(close), np.nan)
    for i in range(2, len(close)):
        impulse = close[i] - close[i - 1]
        prior = close[i - 1] - close[i - 2]
        if impulse > 0 and prior < 0:
            out[i] = 1.0
        elif impulse < 0 and prior > 0:
            out[i] = -1.0
        else:
            out[i] = 0.0
    return out


def _market_structure(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    out = np.full(len(high), np.nan)
    for i in range(5, len(high)):
        hh = high[i] > high[i - 5 : i].max()
        hl = low[i] > low[i - 5 : i].min()
        ll = low[i] < low[i - 5 : i].min()
        lh = high[i] < high[i - 5 : i].max()
        if hh and hl:
            out[i] = 1.0
        elif ll and lh:
            out[i] = -1.0
        else:
            out[i] = 0.0
    return out

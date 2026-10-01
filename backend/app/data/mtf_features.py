"""STEP 2: leakage-safe multi-timeframe XAUUSD features. No labels, no fills."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .litefinance import sha256_file

SYMBOL = "XAUUSD"
SOURCE = "litefinance"
BASE_TIMEFRAME = "H1"
LITEFINANCE_DIR = Path("data") / "processed" / "litefinance"
ML_DIR = Path("data") / "processed" / "ml"

TF_DELTA = {
    "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
    "M15": pd.Timedelta(minutes=15),
}

METADATA_COLUMNS = [
    "timestamp",
    "h4_timestamp",
    "m15_timestamp",
    "symbol",
    "timeframe",
    "source",
]

# Closed H1 OHLC/volume are known at this bar's close (timestamp + 1h).
BASE_COLUMNS = ["open", "high", "low", "close", "tick_volume"]

H1_FEATURE_COLUMNS = [
    "h1_ret_1",
    "h1_log_ret_1",
    "h1_ret_4",
    "h1_ret_24",
    "h1_body",
    "h1_range",
    "h1_upper_wick",
    "h1_lower_wick",
    "h1_body_ratio",
    "h1_close_loc",
    "h1_sma_20",
    "h1_sma_50",
    "h1_sma_200",
    "h1_ema_12",
    "h1_ema_20",
    "h1_ema_50",
    "h1_trend_ema",
    "h1_close_vs_sma20",
    "h1_close_vs_sma50",
    "h1_close_vs_sma200",
    "h1_rsi_14",
    "h1_macd",
    "h1_macd_signal",
    "h1_macd_hist",
    "h1_atr_14",
    "h1_atr_pct",
    "h1_vol_20",
    "h1_range_ma_20",
    "h1_rel_volume_20",
    "h1_hour",
    "h1_dow",
    "h1_gap_hours",
]

H4_FEATURE_COLUMNS = [
    "h4_close",
    "h4_tick_volume",
    "h4_ret_1",
    "h4_log_ret_1",
    "h4_ret_4",
    "h4_body",
    "h4_range",
    "h4_upper_wick",
    "h4_lower_wick",
    "h4_body_ratio",
    "h4_close_loc",
    "h4_sma_20",
    "h4_sma_50",
    "h4_ema_20",
    "h4_ema_50",
    "h4_trend_ema",
    "h4_close_vs_sma20",
    "h4_close_vs_sma50",
    "h4_rsi_14",
    "h4_macd",
    "h4_macd_signal",
    "h4_macd_hist",
    "h4_atr_14",
    "h4_atr_pct",
    "h4_vol_20",
    "h4_rel_volume_20",
    "h4_age_hours",
]

M15_FEATURE_COLUMNS = [
    "m15_close",
    "m15_tick_volume",
    "m15_ret_1",
    "m15_log_ret_1",
    "m15_body",
    "m15_range",
    "m15_upper_wick",
    "m15_lower_wick",
    "m15_body_ratio",
    "m15_close_loc",
    "m15_sma_20",
    "m15_ema_20",
    "m15_ema_50",
    "m15_trend_ema",
    "m15_close_vs_sma20",
    "m15_rsi_14",
    "m15_macd_hist",
    "m15_atr_14",
    "m15_atr_pct",
    "m15_vol_20",
    "m15_rel_volume_20",
    "m15_bars_in_h1",
    "m15_age_minutes",
]

FEATURE_COLUMNS = BASE_COLUMNS + H1_FEATURE_COLUMNS + H4_FEATURE_COLUMNS + M15_FEATURE_COLUMNS
OUTPUT_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS
STEP1_FILES = ("XAUUSD_H1.csv", "XAUUSD_H4.csv", "XAUUSD_M15.csv")


def step1_paths(root: Path) -> dict[str, Path]:
    folder = root / LITEFINANCE_DIR
    return {name: folder / name for name in STEP1_FILES}


def _require_step1(root: Path) -> dict[str, Path]:
    paths = step1_paths(root)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"STEP 1 processed files missing: {missing}")
    return paths


def hash_step1(root: Path) -> dict[str, str]:
    return {name: sha256_file(path) for name, path in _require_step1(root).items()}


def load_tf(path: Path, timeframe: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "tick_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} missing columns {sorted(missing)}")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp", kind="mergesort").drop_duplicates("timestamp", keep="last")
    for col in ["open", "high", "low", "close", "tick_volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close", "tick_volume"]).reset_index(drop=True)
    df["available_at"] = df["timestamp"] + TF_DELTA[timeframe]
    return df


def _safe_div(numer: pd.Series, denom: pd.Series, fill: float = 0.0) -> pd.Series:
    out = numer / denom.replace(0, np.nan)
    return out.fillna(fill)


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rsi = 100.0 - 100.0 / (1.0 + _safe_div(avg_gain, avg_loss, fill=np.nan))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
    return rsi


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = _true_range(high, low, close)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast = close.ewm(span=12, min_periods=12, adjust=False).mean()
    slow = close.ewm(span=26, min_periods=26, adjust=False).mean()
    line = fast - slow
    signal = line.ewm(span=9, min_periods=9, adjust=False).mean()
    return line, signal, line - signal


def add_causal_features(df: pd.DataFrame, prefix: str, *, include_calendar: bool = False) -> pd.DataFrame:
    """Trailing-only indicators on the supplied bars. Never uses centered windows or future rows."""
    out = df.copy()
    o = out["open"]
    high = out["high"]
    low = out["low"]
    close = out["close"]
    volume = out["tick_volume"]
    body = close - o
    rng = high - low
    out[f"{prefix}ret_1"] = close.pct_change(1)
    out[f"{prefix}log_ret_1"] = np.log(close / close.shift(1))
    if prefix == "h1_":
        out[f"{prefix}ret_4"] = close.pct_change(4)
        out[f"{prefix}ret_24"] = close.pct_change(24)
    elif prefix == "h4_":
        out[f"{prefix}ret_4"] = close.pct_change(4)
    out[f"{prefix}body"] = body
    out[f"{prefix}range"] = rng
    out[f"{prefix}upper_wick"] = high - np.maximum(o, close)
    out[f"{prefix}lower_wick"] = np.minimum(o, close) - low
    out[f"{prefix}body_ratio"] = _safe_div(body.abs(), rng, fill=0.0)
    out[f"{prefix}close_loc"] = _safe_div(close - low, rng, fill=0.5)
    out[f"{prefix}sma_20"] = close.rolling(20, min_periods=20).mean()
    out[f"{prefix}ema_20"] = close.ewm(span=20, min_periods=20, adjust=False).mean()
    if prefix != "m15_":
        out[f"{prefix}sma_50"] = close.rolling(50, min_periods=50).mean()
        out[f"{prefix}ema_50"] = close.ewm(span=50, min_periods=50, adjust=False).mean()
        out[f"{prefix}close_vs_sma50"] = close / out[f"{prefix}sma_50"] - 1.0
    else:
        out[f"{prefix}ema_50"] = close.ewm(span=50, min_periods=50, adjust=False).mean()
    if prefix == "h1_":
        out[f"{prefix}sma_200"] = close.rolling(200, min_periods=200).mean()
        out[f"{prefix}ema_12"] = close.ewm(span=12, min_periods=12, adjust=False).mean()
        out[f"{prefix}close_vs_sma200"] = close / out[f"{prefix}sma_200"] - 1.0
    out[f"{prefix}trend_ema"] = (out[f"{prefix}ema_20"] - out[f"{prefix}ema_50"]) / close
    out[f"{prefix}close_vs_sma20"] = close / out[f"{prefix}sma_20"] - 1.0
    out[f"{prefix}rsi_14"] = _rsi(close, 14)
    macd, signal, hist = _macd(close)
    if prefix != "m15_":
        out[f"{prefix}macd"] = macd
        out[f"{prefix}macd_signal"] = signal
    out[f"{prefix}macd_hist"] = hist
    out[f"{prefix}atr_14"] = _atr(high, low, close, 14)
    out[f"{prefix}atr_pct"] = out[f"{prefix}atr_14"] / close
    out[f"{prefix}vol_20"] = out[f"{prefix}ret_1"].rolling(20, min_periods=20).std()
    if prefix == "h1_":
        out[f"{prefix}range_ma_20"] = rng.rolling(20, min_periods=20).mean()
    vol_ma = volume.rolling(20, min_periods=20).mean()
    out[f"{prefix}rel_volume_20"] = _safe_div(volume, vol_ma, fill=np.nan)
    if include_calendar:
        out[f"{prefix}hour"] = out["timestamp"].dt.hour.astype("int16")
        out[f"{prefix}dow"] = out["timestamp"].dt.dayofweek.astype("int16")
        out[f"{prefix}gap_hours"] = out["timestamp"].diff() / pd.Timedelta(hours=1)
    return out


def _m15_bars_in_h1(h1_ts: pd.Series, m15_ts: pd.Series) -> np.ndarray:
    m15_values = m15_ts.to_numpy()
    left = np.searchsorted(m15_values, h1_ts.to_numpy(), side="left")
    last_open = (h1_ts + pd.Timedelta(minutes=45)).to_numpy()
    right = np.searchsorted(m15_values, last_open, side="right")
    return (right - left).astype(np.int16)


def build_feature_frame(h1: pd.DataFrame, h4: pd.DataFrame, m15: pd.DataFrame) -> pd.DataFrame:
    """One row per closed H1 bar. H4/M15 attached only if already available at H1 close."""
    left = add_causal_features(h1, "h1_", include_calendar=True)
    right_h4 = add_causal_features(h4, "h4_")
    right_m15 = add_causal_features(m15, "m15_")

    h4_join = right_h4.rename(columns={"timestamp": "h4_timestamp", "close": "h4_close", "tick_volume": "h4_tick_volume"})
    h4_cols = ["available_at", "h4_timestamp", "h4_close", "h4_tick_volume"] + [c for c in H4_FEATURE_COLUMNS if c not in {"h4_close", "h4_tick_volume", "h4_age_hours"}]
    h4_join = h4_join[h4_cols].sort_values("available_at")

    m15_join = right_m15.rename(columns={"timestamp": "m15_timestamp", "close": "m15_close", "tick_volume": "m15_tick_volume"})
    m15_cols = ["available_at", "m15_timestamp", "m15_close", "m15_tick_volume"] + [
        c for c in M15_FEATURE_COLUMNS if c not in {"m15_close", "m15_tick_volume", "m15_bars_in_h1", "m15_age_minutes"}
    ]
    m15_join = m15_join[m15_cols].sort_values("available_at")

    left = left.sort_values("available_at")
    out = pd.merge_asof(left, h4_join, on="available_at", direction="backward", allow_exact_matches=True)
    out = pd.merge_asof(out, m15_join, on="available_at", direction="backward", allow_exact_matches=True)
    out["h4_age_hours"] = (out["available_at"] - (out["h4_timestamp"] + TF_DELTA["H4"])) / pd.Timedelta(hours=1)
    out["m15_age_minutes"] = (out["available_at"] - (out["m15_timestamp"] + TF_DELTA["M15"])) / pd.Timedelta(minutes=1)
    out["m15_bars_in_h1"] = _m15_bars_in_h1(out["timestamp"], m15["timestamp"])
    out["symbol"] = SYMBOL
    out["timeframe"] = BASE_TIMEFRAME
    out["source"] = SOURCE
    return out


def drop_incomplete(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Remove warm-up / missing-context rows. Never interpolate."""
    counts = {
        "h1_input_rows": int(len(frame)),
        "missing_h4_context": int(frame["h4_timestamp"].isna().sum()),
        "missing_m15_context": int(frame["m15_timestamp"].isna().sum()),
    }
    complete = frame.dropna(subset=["h4_timestamp", "m15_timestamp"]).copy()
    feature_na = complete[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).isna().any(axis=1)
    counts["indicator_warmup"] = int(feature_na.sum())
    clean = complete.loc[~feature_na].copy()
    counts["final_rows"] = int(len(clean))
    counts["removed_total"] = counts["h1_input_rows"] - counts["final_rows"]
    return clean.reset_index(drop=True), counts


def validate_features(frame: pd.DataFrame, h1: pd.DataFrame | None = None, h4: pd.DataFrame | None = None, m15: pd.DataFrame | None = None) -> list[str]:
    errors: list[str] = []
    if frame.empty:
        return ["feature dataset is empty"]
    missing = [col for col in OUTPUT_COLUMNS if col not in frame.columns]
    if missing:
        return [f"missing columns: {missing}"]

    ts = pd.to_datetime(frame["timestamp"])
    if int(ts.duplicated().sum()):
        errors.append(f"duplicate timestamps: {int(ts.duplicated().sum())}")
    if not bool(ts.is_monotonic_increasing):
        errors.append("timestamps are not chronological")
    feats = frame[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if int(feats.isna().sum().sum()):
        errors.append("null feature values present")
    if int(np.isinf(feats.to_numpy(dtype=float)).sum()):
        errors.append("infinite feature values present")

    h1_avail = ts + TF_DELTA["H1"]
    h4_ts = pd.to_datetime(frame["h4_timestamp"])
    m15_ts = pd.to_datetime(frame["m15_timestamp"])
    h4_avail = h4_ts + TF_DELTA["H4"]
    m15_avail = m15_ts + TF_DELTA["M15"]
    if bool((h4_avail > h1_avail).any()):
        errors.append("H4 context uses a bar not yet closed at H1 close")
    if bool((m15_avail > h1_avail).any()):
        errors.append("M15 context uses a bar not yet closed at H1 close")
    if bool((h4_ts >= ts).any()):
        errors.append("H4 context uses a bar that has not closed before the H1 bar")
    if bool((frame["h4_age_hours"] < -1e-9).any() | (frame["m15_age_minutes"] < -1e-9).any()):
        errors.append("negative context age (future alignment)")
    if bool((frame["m15_bars_in_h1"] < 0).any() | (frame["m15_bars_in_h1"] > 4).any()):
        errors.append("m15_bars_in_h1 must be between 0 and 4 without synthesized candles")

    if h1 is not None:
        extra = set(ts) - set(pd.to_datetime(h1["timestamp"]))
        if extra:
            errors.append(f"feature rows not present in H1 source: {len(extra)}")
    if h4 is not None:
        extra_h4 = set(h4_ts) - set(pd.to_datetime(h4["timestamp"]))
        if extra_h4:
            errors.append("H4 timestamps were synthesized")
    if m15 is not None:
        extra_m15 = set(m15_ts) - set(pd.to_datetime(m15["timestamp"]))
        if extra_m15:
            errors.append("M15 timestamps were synthesized")
    return errors


def features_at_or_before(h1: pd.DataFrame, h4: pd.DataFrame, m15: pd.DataFrame, available_at: pd.Timestamp) -> pd.DataFrame:
    """Rebuild features using only candles whose close time is <= available_at."""
    h1_cut = h1.loc[h1["available_at"] <= available_at].copy()
    h4_cut = h4.loc[h4["available_at"] <= available_at].copy()
    m15_cut = m15.loc[m15["available_at"] <= available_at].copy()
    framed, _ = drop_incomplete(build_feature_frame(h1_cut, h4_cut, m15_cut))
    return framed


def write_features_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame[OUTPUT_COLUMNS].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    out["h4_timestamp"] = pd.to_datetime(out["h4_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    out["m15_timestamp"] = pd.to_datetime(out["m15_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    out.to_csv(path, index=False)


def run_step2(root: Path) -> dict[str, Any]:
    step1 = _require_step1(root)
    hashes_before = {name: sha256_file(path) for name, path in step1.items()}
    h1 = load_tf(step1["XAUUSD_H1.csv"], "H1")
    h4 = load_tf(step1["XAUUSD_H4.csv"], "H4")
    m15 = load_tf(step1["XAUUSD_M15.csv"], "M15")

    built = build_feature_frame(h1, h4, m15)
    features, removed = drop_incomplete(built)
    errors = validate_features(features, h1=h1, h4=h4, m15=m15)
    warnings: list[str] = []
    if removed["missing_m15_context"]:
        warnings.append(
            f"Dropped {removed['missing_m15_context']} H1 rows with no closed M15 context "
            "(M15 history starts 2022-07-01; missing M15 bars were not synthesized)."
        )
    if removed["missing_h4_context"]:
        warnings.append(f"Dropped {removed['missing_h4_context']} H1 rows with no closed H4 context.")
    if removed["indicator_warmup"]:
        warnings.append(
            f"Dropped {removed['indicator_warmup']} rows for trailing-indicator warm-up "
            "(SMA/EMA/RSI/MACD/ATR/volume windows; no centered windows)."
        )
    warnings.append(
        "Bar-to-bar returns cross real market gaps (weekends/holidays) using the previous existing bar; "
        "gap hours were not filled with synthetic candles."
    )

    out_dir = root / ML_DIR
    out_path = out_dir / "XAUUSD_features.csv"
    write_features_csv(features, out_path)
    reloaded = pd.read_csv(out_path)
    errors.extend(validate_features(reloaded, h1=h1, h4=h4, m15=m15))

    hashes_after = {name: sha256_file(path) for name, path in step1.items()}
    if hashes_after != hashes_before:
        errors.append("STEP 1 processed files were modified")

    ts = pd.to_datetime(features["timestamp"])
    summary = {
        "step": 2,
        "ok": not errors,
        "output_path": str(out_path),
        "final_rows": int(len(features)),
        "feature_count": len(FEATURE_COLUMNS),
        "feature_list": FEATURE_COLUMNS,
        "date_min": str(ts.min()) if len(features) else None,
        "date_max": str(ts.max()) if len(features) else None,
        "removed": removed,
        "warnings": warnings,
        "errors": errors,
        "base_timeframe": BASE_TIMEFRAME,
        "alignment": "asof_on_candle_close_time",
        "labels_created": False,
        "model_trained": False,
        "step1_sha256_before": hashes_before,
        "step1_sha256_after": hashes_after,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "step2_audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "XAUUSD_features.manifest.json").write_text(
        json.dumps({"feature_count": len(FEATURE_COLUMNS), "columns": OUTPUT_COLUMNS, "features": FEATURE_COLUMNS}, indent=2),
        encoding="utf-8",
    )
    return summary

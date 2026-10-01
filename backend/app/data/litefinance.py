"""STEP 1: audit and clean LiteFinance XAUUSD OHLC files without filling gaps."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

SYMBOL = "XAUUSD"
SOURCE = "litefinance"
RAW_SUBDIR = Path("data") / "raw" / "litefinance"
PROCESSED_SUBDIR = Path("data") / "processed" / "litefinance"

RAW_NAME_CANDIDATES: dict[str, tuple[str, ...]] = {
    "H1": ("XAUUSD_H1.csv", "XAUUSD_H1_LiteFinance.csv"),
    "H4": ("XAUUSD_H4.csv", "XAUUSD_H4_LiteFinance.csv"),
    "M15": ("XAUUSD_M15.csv", "XAUUSD_M15_LiteFinance.csv"),
}

SCOPE: dict[str, dict[str, Any]] = {
    "H1": {
        "start": pd.Timestamp("2009-01-01"),
        "end": pd.Timestamp("2026-12-31 23:59:59"),
        "delta": pd.Timedelta(hours=1),
        "expected_minutes": {0},
        "expected_hours": None,
    },
    "H4": {
        "start": pd.Timestamp("2009-01-01"),
        "end": pd.Timestamp("2026-12-31 23:59:59"),
        "delta": pd.Timedelta(hours=4),
        "expected_minutes": {0},
        "expected_hours": {0, 4, 8, 12, 16, 20},
    },
    "M15": {
        "start": pd.Timestamp("2022-01-01"),
        "end": pd.Timestamp("2026-12-31 23:59:59"),
        "delta": pd.Timedelta(minutes=15),
        "expected_minutes": {0, 15, 30, 45},
        "expected_hours": None,
    },
}

XAUUSD_MIN_PRICE = 200.0
XAUUSD_MAX_PRICE = 10_000.0
REAL_VOLUME_CORRUPT_THRESHOLD = 1_000_000_000
SPREAD_EXTREME_WARN = 1_000
MT_EXPORT_ROW_CAP = 100_000
PROCESSED_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
    "symbol",
    "timeframe",
    "source",
]


@dataclass
class CleanResult:
    timeframe: str
    raw_path: Path
    processed_path: Path
    audit_path: Path
    raw_sha256: str
    raw_rows: int
    processed_rows: int
    date_min: str | None
    date_max: str | None
    removed: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    gap_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "raw_path": str(self.raw_path),
            "processed_path": str(self.processed_path),
            "raw_sha256": self.raw_sha256,
            "raw_rows": self.raw_rows,
            "processed_rows": self.processed_rows,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "removed": self.removed,
            "warnings": self.warnings,
            "errors": self.errors,
            "gap_stats": self.gap_stats,
            "never_modified_raw": True,
            "never_created_candles": True,
        }


def repo_root_from(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "scripts").is_dir() and (candidate / "backend" / "app").is_dir() and (candidate / "data" / "raw").exists():
            return candidate
    return Path(__file__).resolve().parents[3]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_raw_path(root: Path, timeframe: str) -> Path:
    directory = root / RAW_SUBDIR
    for name in RAW_NAME_CANDIDATES[timeframe]:
        path = directory / name
        if path.is_file():
            return path
    expected = ", ".join(RAW_NAME_CANDIDATES[timeframe])
    raise FileNotFoundError(f"Missing LiteFinance {timeframe} CSV in {directory} (tried {expected})")


def _empty_removed() -> dict[str, int]:
    return {
        "unparseable_timestamp": 0,
        "out_of_scope": 0,
        "duplicate_timestamp": 0,
        "null_required": 0,
        "non_positive_price": 0,
        "price_out_of_range": 0,
        "ohlc_invalid": 0,
        "negative_tick_volume": 0,
        "negative_spread": 0,
        "misaligned_timeframe": 0,
    }


def _record_drop(removed: dict[str, int], reason: str, mask: pd.Series) -> pd.Series:
    count = int(mask.sum())
    removed[reason] += count
    return ~mask


def _parse_timestamp(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, format="%Y.%m.%d %H:%M", errors="coerce")
    still_na = parsed.isna() & series.notna()
    if still_na.any():
        parsed = parsed.fillna(pd.to_datetime(series[still_na], errors="coerce"))
    return parsed


def _ohlc_invalid(df: pd.DataFrame) -> pd.Series:
    return (
        (df["high"] < df[["open", "close", "low"]].max(axis=1))
        | (df["low"] > df[["open", "close", "high"]].min(axis=1))
    )


def _aligned(ts: pd.Series, timeframe: str) -> pd.Series:
    spec = SCOPE[timeframe]
    ok = ts.dt.second.fillna(0).eq(0) & ts.dt.minute.isin(spec["expected_minutes"])
    hours = spec["expected_hours"]
    if hours is not None:
        ok &= ts.dt.hour.isin(hours)
    return ok


def _gap_stats(timestamps: pd.Series, timeframe: str) -> dict[str, Any]:
    spec = SCOPE[timeframe]
    ordered = timestamps.sort_values()
    deltas = ordered.diff().dropna()
    extra = deltas[deltas > spec["delta"]]
    weekend = extra[(extra >= pd.Timedelta(hours=36)) & (extra <= pd.Timedelta(hours=72))]
    long_gaps = extra[extra > pd.Timedelta(days=3)]
    examples = []
    if not extra.empty:
        prev = ordered.shift(1)
        for idx in extra.nlargest(min(8, len(extra))).index:
            examples.append(
                {
                    "from": prev.loc[idx].isoformat(sep=" "),
                    "to": ordered.loc[idx].isoformat(sep=" "),
                    "hours": round(extra.loc[idx] / pd.Timedelta(hours=1), 2),
                }
            )
    return {
        "expected_delta": str(spec["delta"]),
        "gap_count": int(len(extra)),
        "weekend_like_gaps": int(len(weekend)),
        "gaps_over_3_days": int(len(long_gaps)),
        "max_gap": str(extra.max()) if not extra.empty else str(spec["delta"]),
        "examples": examples,
    }


def clean_frame(raw: pd.DataFrame, timeframe: str) -> tuple[pd.DataFrame, dict[str, int], list[str], list[str]]:
    """Drop invalid rows only. Never interpolate or insert missing candles."""
    warnings: list[str] = []
    errors: list[str] = []
    removed = _empty_removed()
    spec = SCOPE[timeframe]
    df = raw.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    required = ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
    missing_cols = [col for col in required if col not in df.columns]
    if missing_cols:
        errors.append(f"{timeframe} missing columns: {missing_cols}")
        return pd.DataFrame(columns=PROCESSED_COLUMNS), removed, warnings, errors

    df["timestamp"] = _parse_timestamp(df["time"])
    keep = _record_drop(removed, "unparseable_timestamp", df["timestamp"].isna())
    df = df.loc[keep].copy()

    keep = _record_drop(
        removed,
        "out_of_scope",
        (df["timestamp"] < spec["start"]) | (df["timestamp"] > spec["end"]),
    )
    df = df.loc[keep].copy()

    for col in ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    keep = _record_drop(
        removed,
        "null_required",
        df[["timestamp", "open", "high", "low", "close", "tick_volume", "spread"]].isna().any(axis=1),
    )
    df = df.loc[keep].copy()

    df = df.sort_values("timestamp", kind="mergesort")
    dup_mask = df["timestamp"].duplicated(keep="last")
    keep = _record_drop(removed, "duplicate_timestamp", dup_mask)
    df = df.loc[keep].copy()

    prices = df[["open", "high", "low", "close"]]
    keep = _record_drop(removed, "non_positive_price", (prices <= 0).any(axis=1))
    df = df.loc[keep].copy()

    prices = df[["open", "high", "low", "close"]]
    keep = _record_drop(
        removed,
        "price_out_of_range",
        (prices.min(axis=1) < XAUUSD_MIN_PRICE) | (prices.max(axis=1) > XAUUSD_MAX_PRICE),
    )
    df = df.loc[keep].copy()

    keep = _record_drop(removed, "ohlc_invalid", _ohlc_invalid(df))
    df = df.loc[keep].copy()

    keep = _record_drop(removed, "negative_tick_volume", df["tick_volume"] < 0)
    df = df.loc[keep].copy()

    keep = _record_drop(removed, "negative_spread", df["spread"] < 0)
    df = df.loc[keep].copy()

    keep = _record_drop(removed, "misaligned_timeframe", ~_aligned(df["timestamp"], timeframe))
    df = df.loc[keep].copy()

    df["real_volume"] = df["real_volume"].fillna(0)
    corrupt_volume = df["real_volume"] >= REAL_VOLUME_CORRUPT_THRESHOLD
    corrupt_count = int(corrupt_volume.sum())
    if corrupt_count:
        df.loc[corrupt_volume, "real_volume"] = 0
        warnings.append(
            f"{timeframe}: set {corrupt_count} corrupt real_volume values (>= {REAL_VOLUME_CORRUPT_THRESHOLD}) to 0"
        )
    negative_real = df["real_volume"] < 0
    if int(negative_real.sum()):
        df.loc[negative_real, "real_volume"] = 0
        warnings.append(f"{timeframe}: set {int(negative_real.sum())} negative real_volume values to 0")

    extreme_spread = int((df["spread"] > SPREAD_EXTREME_WARN).sum())
    if extreme_spread:
        warnings.append(f"{timeframe}: {extreme_spread} bars have spread > {SPREAD_EXTREME_WARN} (kept)")

    zero_spread = int((df["spread"] == 0).sum())
    if zero_spread:
        warnings.append(f"{timeframe}: {zero_spread} bars have spread=0 (kept; common on older LiteFinance exports)")

    zero_real = int((df["real_volume"] == 0).sum())
    if zero_real:
        warnings.append(
            f"{timeframe}: {zero_real}/{len(df)} bars have real_volume=0 (kept; tick_volume is the activity field)"
        )

    df["tick_volume"] = df["tick_volume"].astype("int64")
    df["spread"] = df["spread"].astype("int64")
    df["real_volume"] = df["real_volume"].astype("int64")
    df["symbol"] = SYMBOL
    df["timeframe"] = timeframe
    df["source"] = SOURCE
    cleaned = df[PROCESSED_COLUMNS].reset_index(drop=True)
    if cleaned.empty:
        errors.append(f"{timeframe}: no rows remained after cleaning")
    return cleaned, removed, warnings, errors


def write_processed_csv(df: pd.DataFrame, path: Path, raw_dir: Path | None = None) -> None:
    resolved = path.resolve()
    if raw_dir is not None and resolved.is_relative_to(raw_dir.resolve()):
        raise RuntimeError("Refusing to write processed data under data/raw")
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    out.to_csv(path, index=False)


def validate_processed(df: pd.DataFrame, timeframe: str) -> list[str]:
    errors: list[str] = []
    spec = SCOPE[timeframe]
    if df.empty:
        return [f"{timeframe}: processed file is empty"]
    missing = [col for col in PROCESSED_COLUMNS if col not in df.columns]
    if missing:
        return [f"{timeframe}: processed file missing columns {missing}"]

    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    if int(ts.isna().sum()):
        errors.append(f"{timeframe}: {int(ts.isna().sum())} unparseable processed timestamps")
    if not bool(ts.is_monotonic_increasing):
        errors.append(f"{timeframe}: timestamps are not strictly increasing")
    if int(ts.duplicated().sum()):
        errors.append(f"{timeframe}: {int(ts.duplicated().sum())} duplicate timestamps")
    if int(df[PROCESSED_COLUMNS].isna().sum().sum()):
        errors.append(f"{timeframe}: nulls present in processed file")

    prices = df[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    if int((prices <= 0).any(axis=1).sum()):
        errors.append(f"{timeframe}: non-positive OHLC prices")
    if int(((prices.min(axis=1) < XAUUSD_MIN_PRICE) | (prices.max(axis=1) > XAUUSD_MAX_PRICE)).sum()):
        errors.append(f"{timeframe}: prices outside XAUUSD range {XAUUSD_MIN_PRICE}-{XAUUSD_MAX_PRICE}")
    ohlc_bad = (prices["high"] < prices[["open", "close", "low"]].max(axis=1)) | (
        prices["low"] > prices[["open", "close", "high"]].min(axis=1)
    )
    if int(ohlc_bad.sum()):
        errors.append(f"{timeframe}: OHLC consistency violations")

    tick = pd.to_numeric(df["tick_volume"], errors="coerce")
    spread = pd.to_numeric(df["spread"], errors="coerce")
    real = pd.to_numeric(df["real_volume"], errors="coerce")
    if int((tick < 0).sum()):
        errors.append(f"{timeframe}: negative tick_volume")
    if int((spread < 0).sum()):
        errors.append(f"{timeframe}: negative spread")
    if int((real < 0).sum()):
        errors.append(f"{timeframe}: negative real_volume")
    if int((real >= REAL_VOLUME_CORRUPT_THRESHOLD).sum()):
        errors.append(f"{timeframe}: corrupt real_volume remains")
    if int((~_aligned(ts, timeframe)).sum()):
        errors.append(f"{timeframe}: bars not aligned to {timeframe} grid")
    if ts.min() < spec["start"] or ts.max() > spec["end"]:
        errors.append(f"{timeframe}: timestamps outside requested scope")
    if int((df["symbol"] != SYMBOL).sum()) or int((df["timeframe"] != timeframe).sum()):
        errors.append(f"{timeframe}: symbol/timeframe labels incorrect")
    if int((df["source"] != SOURCE).sum()):
        errors.append(f"{timeframe}: source must be litefinance")
    deltas = ts.diff().dropna()
    if not deltas.empty and bool((deltas < spec["delta"]).any()):
        errors.append(f"{timeframe}: intervals shorter than {spec['delta']} (possible duplicates or inserts)")
    return errors


def _scope_coverage_warnings(df: pd.DataFrame, timeframe: str, raw_rows: int) -> list[str]:
    warnings: list[str] = []
    spec = SCOPE[timeframe]
    ts = pd.to_datetime(df["timestamp"])
    if ts.min() > spec["start"] + pd.Timedelta(days=7):
        warnings.append(
            f"{timeframe}: first bar is {ts.min()} while requested start is {spec['start'].date()} "
            "(raw export does not cover the full window; candles were not synthesized)"
        )
    if ts.max() < pd.Timestamp("2026-01-01"):
        warnings.append(f"{timeframe}: last bar is {ts.max()} which is before 2026")
    if raw_rows >= MT_EXPORT_ROW_CAP:
        warnings.append(
            f"{timeframe}: raw file has {raw_rows} rows (MetaTrader export cap is often {MT_EXPORT_ROW_CAP}); "
            "history may be truncated"
        )
    return warnings


def process_timeframe(root: Path, timeframe: str) -> CleanResult:
    raw_path = resolve_raw_path(root, timeframe)
    processed_dir = root / PROCESSED_SUBDIR
    processed_path = processed_dir / f"XAUUSD_{timeframe}.csv"
    audit_path = processed_dir / f"XAUUSD_{timeframe}.audit.json"
    if processed_path.resolve().is_relative_to((root / RAW_SUBDIR).resolve()):
        raise RuntimeError("Processed output path resolved inside data/raw")

    raw_hash_before = sha256_file(raw_path)
    raw = pd.read_csv(raw_path)
    cleaned, removed, warnings, errors = clean_frame(raw, timeframe)
    if not cleaned.empty:
        warnings.extend(_scope_coverage_warnings(cleaned, timeframe, len(raw)))
        gap_stats = _gap_stats(pd.to_datetime(cleaned["timestamp"]), timeframe)
        if gap_stats["gap_count"]:
            warnings.append(
                f"{timeframe}: preserved {gap_stats['gap_count']} real gaps "
                f"(weekend-like={gap_stats['weekend_like_gaps']}, >3d={gap_stats['gaps_over_3_days']})"
            )
        write_processed_csv(cleaned, processed_path, raw_dir=root / RAW_SUBDIR)
        errors.extend(validate_processed(pd.read_csv(processed_path), timeframe))
        date_min = str(pd.to_datetime(cleaned["timestamp"]).min())
        date_max = str(pd.to_datetime(cleaned["timestamp"]).max())
    else:
        gap_stats = {}
        date_min = None
        date_max = None
        processed_dir.mkdir(parents=True, exist_ok=True)

    raw_hash_after = sha256_file(raw_path)
    if raw_hash_after != raw_hash_before:
        errors.append(f"{timeframe}: raw file hash changed during processing")

    result = CleanResult(
        timeframe=timeframe,
        raw_path=raw_path,
        processed_path=processed_path,
        audit_path=audit_path,
        raw_sha256=raw_hash_before,
        raw_rows=len(raw),
        processed_rows=len(cleaned),
        date_min=date_min,
        date_max=date_max,
        removed=removed,
        warnings=warnings,
        errors=errors,
        gap_stats=gap_stats,
    )
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return result


def run_step1(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root_from()
    started = datetime.now().isoformat(timespec="seconds")
    results = [process_timeframe(root, timeframe) for timeframe in ("H1", "H4", "M15")]
    summary = {
        "step": 1,
        "started_at": started,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "source": SOURCE,
        "symbol": SYMBOL,
        "raw_untouched": True,
        "candles_synthesized": False,
        "timeframes": [item.to_dict() for item in results],
        "errors": [err for item in results for err in item.errors],
        "ok": all(not item.errors for item in results),
    }
    report_path = root / PROCESSED_SUBDIR / "step1_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["report_path"] = str(report_path)
    return summary

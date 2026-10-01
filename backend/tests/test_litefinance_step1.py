"""STEP 1 tests: LiteFinance XAUUSD cleaning without synthesizing candles."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.data.litefinance import (
    PROCESSED_COLUMNS,
    SCOPE,
    SYMBOL,
    clean_frame,
    resolve_raw_path,
    repo_root_from,
    run_step1,
    sha256_file,
    validate_processed,
    write_processed_csv,
)

ROOT = repo_root_from(Path(__file__))


def _raw_row(time: str, open_: float = 1800, high: float = 1805, low: float = 1795, close: float = 1802, **extra):
    row = {
        "time": time,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "tick_volume": extra.get("tick_volume", 10),
        "spread": extra.get("spread", 5),
        "real_volume": extra.get("real_volume", 0),
    }
    return row


def test_drops_invalid_rows_and_does_not_insert_gap_candles():
    raw = pd.DataFrame(
        [
            _raw_row("2022.07.01 00:00"),
            _raw_row("2022.07.01 00:00", close=1803),  # duplicate timestamp
            _raw_row("2022.07.01 00:15", high=1790, low=1795, close=1800),  # invalid OHLC
            _raw_row("2022.07.01 00:30", open_=0),  # non-positive
            _raw_row("2022.07.01 00:45", open_=50, high=51, low=49, close=50),  # out of XAUUSD range
            _raw_row("2022.07.01 01:05"),  # misaligned M15
            _raw_row("2022.07.01 01:15", tick_volume=-1),
            _raw_row("2022.07.01 01:30", spread=-2),
            _raw_row("1970.01.05 00:00", open_=35, high=35, low=35, close=35),  # out of scope
            _raw_row("2022.07.01 02:00"),  # kept; gap after 00:00
            _raw_row("2022.07.01 02:00", real_volume=2_000_000_000_000),  # duplicate + corrupt volume
        ]
    )
    cleaned, removed, warnings, errors = clean_frame(raw, "M15")
    assert not errors
    assert list(cleaned["timestamp"].astype(str)) == ["2022-07-01 00:00:00", "2022-07-01 02:00:00"]
    assert cleaned.iloc[-1]["real_volume"] == 0
    assert removed["duplicate_timestamp"] == 2
    assert removed["ohlc_invalid"] == 1
    assert removed["non_positive_price"] == 1
    assert removed["price_out_of_range"] == 1
    assert removed["misaligned_timeframe"] == 1
    assert removed["negative_tick_volume"] == 1
    assert removed["negative_spread"] == 1
    assert removed["out_of_scope"] == 1
    assert validate_processed(cleaned, "M15") == []
    assert any("corrupt real_volume" in item for item in warnings)


def test_h4_alignment_and_scope():
    raw = pd.DataFrame(
        [
            _raw_row("2008.12.31 20:00", open_=850, high=860, low=840, close=855),
            _raw_row("2009.01.01 00:00", open_=880, high=890, low=870, close=885),
            _raw_row("2009.01.01 02:00", open_=880, high=890, low=870, close=885),
            _raw_row("2009.01.01 04:00", open_=885, high=895, low=875, close=890),
        ]
    )
    cleaned, removed, _, errors = clean_frame(raw, "H4")
    assert not errors
    assert removed["out_of_scope"] == 1
    assert removed["misaligned_timeframe"] == 1
    assert list(pd.to_datetime(cleaned["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")) == [
        "2009-01-01 00:00:00",
        "2009-01-01 04:00:00",
    ]


def test_write_processed_refuses_raw_directory(tmp_path: Path):
    df = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp("2022-07-01 00:00:00"),
                "open": 1800.0,
                "high": 1805.0,
                "low": 1795.0,
                "close": 1802.0,
                "tick_volume": 10,
                "spread": 5,
                "real_volume": 0,
                "symbol": SYMBOL,
                "timeframe": "M15",
                "source": "litefinance",
            }
        ]
    )
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    with pytest.raises(RuntimeError, match="data/raw"):
        write_processed_csv(df, raw_dir / "XAUUSD_M15.csv", raw_dir=raw_dir)


def test_processed_subset_of_raw_timestamps_never_invented():
    raw = pd.DataFrame(
        [
            _raw_row("2024.01.02 00:00"),
            _raw_row("2024.01.02 01:00"),
            _raw_row("2024.01.02 03:00"),
        ]
    )
    cleaned, _, _, errors = clean_frame(raw, "H1")
    assert not errors
    raw_ts = set(pd.to_datetime(raw["time"], format="%Y.%m.%d %H:%M"))
    clean_ts = set(pd.to_datetime(cleaned["timestamp"]))
    assert clean_ts <= raw_ts
    assert pd.Timestamp("2024-01-02 02:00:00") not in clean_ts


@pytest.mark.skipif(
    not any((ROOT / "data" / "raw" / "litefinance").glob("XAUUSD_H1*.csv")),
    reason="LiteFinance raw H1 CSV is not present",
)
def test_step1_on_real_litefinance_files():
    hashes_before = {
        tf: sha256_file(resolve_raw_path(ROOT, tf)) for tf in ("H1", "H4", "M15")
    }
    summary = run_step1(ROOT)
    assert summary["ok"], summary["errors"]
    assert summary["candles_synthesized"] is False
    assert summary["raw_untouched"] is True

    for tf in ("H1", "H4", "M15"):
        raw_path = resolve_raw_path(ROOT, tf)
        assert sha256_file(raw_path) == hashes_before[tf]
        processed = ROOT / "data" / "processed" / "litefinance" / f"XAUUSD_{tf}.csv"
        assert processed.is_file()
        df = pd.read_csv(processed)
        errors = validate_processed(df, tf)
        assert errors == [], errors
        assert list(df.columns) == PROCESSED_COLUMNS

        raw = pd.read_csv(raw_path)
        raw["timestamp"] = pd.to_datetime(raw["time"], format="%Y.%m.%d %H:%M", errors="coerce")
        spec = SCOPE[tf]
        in_scope = raw["timestamp"].dropna()
        in_scope = in_scope[(in_scope >= spec["start"]) & (in_scope <= spec["end"])]
        processed_ts = set(pd.to_datetime(df["timestamp"]))
        assert processed_ts <= set(in_scope)
        assert df["symbol"].eq("XAUUSD").all()
        assert df["source"].eq("litefinance").all()
        assert pd.to_datetime(df["timestamp"]).min().year >= spec["start"].year
        assert pd.to_datetime(df["timestamp"]).max().year <= 2026

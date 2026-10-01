"""STEP 2 tests: leakage-safe H1/H4/M15 features, no labels, no candle synthesis."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.data.litefinance import repo_root_from, sha256_file
from app.data.mtf_features import (
    FEATURE_COLUMNS,
    TF_DELTA,
    add_causal_features,
    build_feature_frame,
    drop_incomplete,
    features_at_or_before,
    hash_step1,
    load_tf,
    run_step2,
    step1_paths,
    validate_features,
)

ROOT = repo_root_from(Path(__file__))


def _ohlc_frame(timestamps: pd.DatetimeIndex, start: float = 2000.0, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 0.4, size=len(timestamps))
    close = start + np.cumsum(steps)
    close = np.maximum(close, 1500.0)
    high = close + rng.uniform(0.1, 1.5, size=len(timestamps))
    low = close - rng.uniform(0.1, 1.5, size=len(timestamps))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum.reduce([high, open_, close])
    low = np.minimum.reduce([low, open_, close])
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": rng.integers(100, 500, size=len(timestamps)),
            "available_at": timestamps + pd.Timedelta(hours=1),
        }
    )


def _synthetic_mtf(n_h1: int = 260, seed: int = 1) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    h1_ts = pd.date_range("2024-01-01 00:00:00", periods=n_h1, freq="h")
    h1 = _ohlc_frame(h1_ts, seed=seed)
    h1["available_at"] = h1["timestamp"] + TF_DELTA["H1"]
    h4_ts = pd.date_range(h1_ts[0], h1_ts[-1], freq="4h")
    m15_ts = pd.date_range(h1_ts[0], h1_ts[-1] + pd.Timedelta(minutes=45), freq="15min")
    h4 = _ohlc_frame(h4_ts, start=2000.0, seed=seed + 1)
    h4["available_at"] = h4["timestamp"] + TF_DELTA["H4"]
    m15 = _ohlc_frame(m15_ts, start=2000.0, seed=seed + 2)
    m15["available_at"] = m15["timestamp"] + TF_DELTA["M15"]
    return h1, h4, m15


def test_no_centered_windows_in_source():
    source = (Path(__file__).resolve().parents[1] / "app" / "data" / "mtf_features.py").read_text(encoding="utf-8")
    compact = source.replace(" ", "")
    assert "center=True" not in compact
    assert "rolling(" in source


def test_h4_and_m15_align_to_closed_bars_only():
    h1, h4, m15 = _synthetic_mtf()
    framed = build_feature_frame(h1, h4, m15)
    row = framed.loc[framed["timestamp"] == pd.Timestamp("2024-01-01 16:00:00")].iloc[0]
    assert row["h4_timestamp"] == pd.Timestamp("2024-01-01 12:00:00")
    assert row["m15_timestamp"] == pd.Timestamp("2024-01-01 16:45:00")
    assert row["m15_bars_in_h1"] == 4
    h1_close = pd.Timestamp("2024-01-01 17:00:00")
    assert row["h4_timestamp"] + TF_DELTA["H4"] <= h1_close
    assert row["m15_timestamp"] + TF_DELTA["M15"] <= h1_close


def test_rolling_sma_uses_current_and_past_only():
    h1, h4, m15 = _synthetic_mtf()
    featured = add_causal_features(h1, "h1_", include_calendar=True)
    i = 40
    expected = h1["close"].iloc[i - 19 : i + 1].mean()
    assert featured["h1_sma_20"].iloc[i] == pytest.approx(expected, rel=0, abs=1e-12)
    with_future = h1.copy()
    with_future.loc[i + 1, "close"] = h1.loc[i + 1, "close"] + 500
    mutated = add_causal_features(with_future, "h1_", include_calendar=True)
    assert mutated["h1_sma_20"].iloc[i] == pytest.approx(featured["h1_sma_20"].iloc[i], rel=0, abs=1e-12)


def test_does_not_synthesize_missing_m15_bars():
    h1, h4, m15 = _synthetic_mtf(n_h1=220)
    removed_open = pd.Timestamp("2024-01-02 10:15:00")
    m15 = m15.loc[m15["timestamp"] != removed_open].reset_index(drop=True)
    framed = build_feature_frame(h1, h4, m15)
    row = framed.loc[framed["timestamp"] == pd.Timestamp("2024-01-02 10:00:00")].iloc[0]
    assert row["m15_bars_in_h1"] == 3
    assert pd.Timestamp("2024-01-02 10:15:00") not in set(pd.to_datetime(framed["m15_timestamp"]))


def test_explicit_leakage_future_mutation_does_not_change_features_at_t():
    h1, h4, m15 = _synthetic_mtf(n_h1=280)
    full, _ = drop_incomplete(build_feature_frame(h1, h4, m15))
    assert len(full) > 20
    probe = full.iloc[len(full) // 2]
    t = pd.Timestamp(probe["timestamp"])
    cutoff = t + TF_DELTA["H1"]

    h1_poison = h1.copy()
    h4_poison = h4.copy()
    m15_poison = m15.copy()
    h1_poison.loc[h1_poison["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    h4_poison.loc[h4_poison["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    m15_poison.loc[m15_poison["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    poisoned, _ = drop_incomplete(build_feature_frame(h1_poison, h4_poison, m15_poison))
    truncated = features_at_or_before(h1, h4, m15, cutoff)

    original = full.loc[full["timestamp"] == t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)
    poisoned_row = poisoned.loc[poisoned["timestamp"] == t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)
    truncated_row = truncated.loc[truncated["timestamp"] == t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)
    assert np.allclose(original, poisoned_row, rtol=0, atol=1e-10, equal_nan=False)
    assert np.allclose(original, truncated_row, rtol=0, atol=1e-10, equal_nan=False)


def test_features_are_reproducible():
    h1, h4, m15 = _synthetic_mtf(n_h1=240, seed=7)
    a, _ = drop_incomplete(build_feature_frame(h1, h4, m15))
    b, _ = drop_incomplete(build_feature_frame(h1.copy(), h4.copy(), m15.copy()))
    pd.testing.assert_frame_equal(a[FEATURE_COLUMNS], b[FEATURE_COLUMNS], check_dtype=False)


def test_no_null_inf_duplicates_on_synthetic():
    h1, h4, m15 = _synthetic_mtf(n_h1=260)
    out, _ = drop_incomplete(build_feature_frame(h1, h4, m15))
    errors = validate_features(out, h1=h1, h4=h4, m15=m15)
    assert errors == []
    assert out["timestamp"].is_monotonic_increasing
    assert out["timestamp"].duplicated().sum() == 0


FEATURE_CSV = ROOT / "data" / "processed" / "ml" / "XAUUSD_features.csv"
STEP1_H1 = ROOT / "data" / "processed" / "litefinance" / "XAUUSD_H1.csv"


@pytest.fixture(scope="module")
def real_step2():
    if not STEP1_H1.is_file():
        pytest.skip("STEP 1 H1 file missing")
    before = hash_step1(ROOT)
    summary = run_step2(ROOT)
    after = hash_step1(ROOT)
    df = pd.read_csv(FEATURE_CSV)
    h1 = load_tf(step1_paths(ROOT)["XAUUSD_H1.csv"], "H1")
    h4 = load_tf(step1_paths(ROOT)["XAUUSD_H4.csv"], "H4")
    m15 = load_tf(step1_paths(ROOT)["XAUUSD_M15.csv"], "M15")
    return {"before": before, "after": after, "summary": summary, "df": df, "h1": h1, "h4": h4, "m15": m15}


def test_1_no_duplicate_timestamps(real_step2):
    ts = pd.to_datetime(real_step2["df"]["timestamp"])
    assert ts.duplicated().sum() == 0
    assert bool(ts.is_monotonic_increasing)


def test_2_no_invalid_null_infinite_values(real_step2):
    feats = real_step2["df"][FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    assert int(feats.isna().sum().sum()) == 0
    assert int(np.isinf(feats.to_numpy(dtype=float)).sum()) == 0


def test_3_h1_h4_m15_alignment(real_step2):
    df, h1, h4, m15 = real_step2["df"], real_step2["h1"], real_step2["h4"], real_step2["m15"]
    errors = validate_features(df, h1=h1, h4=h4, m15=m15)
    assert errors == []
    ts = pd.to_datetime(df["timestamp"])
    h4_ts = pd.to_datetime(df["h4_timestamp"])
    m15_ts = pd.to_datetime(df["m15_timestamp"])
    assert (h4_ts + TF_DELTA["H4"] <= ts + TF_DELTA["H1"]).all()
    assert (m15_ts + TF_DELTA["M15"] <= ts + TF_DELTA["H1"]).all()
    assert set(h4_ts).issubset(set(pd.to_datetime(h4["timestamp"])))
    assert set(m15_ts).issubset(set(pd.to_datetime(m15["timestamp"])))


def test_4_no_future_information(real_step2):
    df = real_step2["df"]
    ts = pd.to_datetime(df["timestamp"])
    assert (pd.to_datetime(df["h4_timestamp"]) + TF_DELTA["H4"] <= ts + TF_DELTA["H1"]).all()
    assert (pd.to_datetime(df["m15_timestamp"]) + TF_DELTA["M15"] <= ts + TF_DELTA["H1"]).all()
    assert (df["h4_age_hours"] >= -1e-9).all()
    assert (df["m15_age_minutes"] >= -1e-9).all()


def test_5_no_lookahead_in_rolling_indicators():
    h1, h4, m15 = _synthetic_mtf(n_h1=260)
    featured = add_causal_features(h1, "h1_", include_calendar=True)
    i = 80
    assert featured["h1_sma_20"].iloc[i] == pytest.approx(h1["close"].iloc[i - 19 : i + 1].mean(), abs=1e-12)
    assert featured["h1_sma_50"].iloc[i] == pytest.approx(h1["close"].iloc[i - 49 : i + 1].mean(), abs=1e-12)
    future = h1.copy()
    future.loc[i + 1 :, ["open", "high", "low", "close", "tick_volume"]] = 8888.0
    mutated = add_causal_features(future, "h1_", include_calendar=True)
    cols = [c for c in FEATURE_COLUMNS if c.startswith("h1_")]
    assert np.allclose(
        featured.loc[featured.index <= i, cols].to_numpy(dtype=float),
        mutated.loc[mutated.index <= i, cols].to_numpy(dtype=float),
        rtol=0,
        atol=1e-10,
        equal_nan=True,
    )


def test_6_feature_values_are_reproducible(real_step2):
    rebuilt, _ = drop_incomplete(
        build_feature_frame(real_step2["h1"], real_step2["h4"], real_step2["m15"])
    )
    left = rebuilt[FEATURE_COLUMNS].to_numpy(dtype=float)
    right = real_step2["df"][FEATURE_COLUMNS].to_numpy(dtype=float)
    assert np.allclose(left, right, rtol=1e-10, atol=1e-8, equal_nan=False)


def test_explicit_leakage_remove_and_modify_after_t(real_step2):
    df, h1, h4, m15 = real_step2["df"], real_step2["h1"], real_step2["h4"], real_step2["m15"]
    probe_t = pd.Timestamp(df.iloc[len(df) // 2]["timestamp"])
    cutoff = probe_t + TF_DELTA["H1"]
    original = df.loc[pd.to_datetime(df["timestamp"]) == probe_t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)

    truncated = features_at_or_before(h1, h4, m15, cutoff)
    truncated_row = truncated.loc[truncated["timestamp"] == probe_t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)

    h1_p, h4_p, m15_p = h1.copy(), h4.copy(), m15.copy()
    h1_p.loc[h1_p["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    h4_p.loc[h4_p["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    m15_p.loc[m15_p["available_at"] > cutoff, ["open", "high", "low", "close"]] = 9999.0
    poisoned, _ = drop_incomplete(build_feature_frame(h1_p, h4_p, m15_p))
    poisoned_row = poisoned.loc[poisoned["timestamp"] == probe_t, FEATURE_COLUMNS].iloc[0].to_numpy(dtype=float)

    assert np.allclose(original, truncated_row, rtol=1e-10, atol=1e-8, equal_nan=False)
    assert np.allclose(original, poisoned_row, rtol=1e-10, atol=1e-8, equal_nan=False)


def test_step2_real_litefinance_dataset(real_step2):
    summary = real_step2["summary"]
    assert real_step2["before"] == real_step2["after"]
    assert summary["ok"], summary["errors"]
    assert summary["labels_created"] is False
    assert summary["model_trained"] is False
    assert summary["final_rows"] > 0
    assert FEATURE_CSV.is_file()
    for name, file_path in step1_paths(ROOT).items():
        assert sha256_file(file_path) == real_step2["before"][name]

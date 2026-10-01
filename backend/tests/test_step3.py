"""STEP 3 tests: leakage-safe labels, chronological splits, baseline models."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone

from app.data.litefinance import repo_root_from, sha256_file
from app.data.mtf_features import FEATURE_COLUMNS
from app.ml.step3 import (
    FORBIDDEN_IN_X,
    MODEL_NAMES,
    compare_label_configs,
    chronological_splits,
    feature_matrix,
    features_path,
    load_features,
    make_labels,
    run_step3,
    select_label_config,
    train_models,
    validate_splits,
    validate_xy,
)

ROOT = repo_root_from(Path(__file__))
STEP3_SOURCE = Path(__file__).resolve().parents[1] / "app" / "ml" / "step3.py"


def _synthetic_features(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2023-01-02 00:00:00", periods=n, freq="h")
    close = 1900 + np.cumsum(rng.normal(0, 1.2, size=n))
    high = close + rng.uniform(0.2, 1.5, size=n)
    low = close - rng.uniform(0.2, 1.5, size=n)
    open_ = np.r_[close[0], close[:-1]]
    frame = pd.DataFrame({col: rng.normal(0, 1, size=n) for col in FEATURE_COLUMNS})
    frame["timestamp"] = ts
    frame["h4_timestamp"] = ts
    frame["m15_timestamp"] = ts
    frame["symbol"] = "XAUUSD"
    frame["timeframe"] = "H1"
    frame["source"] = "litefinance"
    frame["open"] = open_
    frame["high"] = np.maximum.reduce([high, open_, close])
    frame["low"] = np.minimum.reduce([low, open_, close])
    frame["close"] = close
    frame["tick_volume"] = rng.integers(50, 400, size=n)
    return frame


def test_no_random_shuffle_in_source():
    source = STEP3_SOURCE.read_text(encoding="utf-8")
    compact = source.replace(" ", "")
    assert "fromsklearn.model_selectionimport" not in compact
    assert "shuffle=True" not in compact
    # Ensure there is no real *import* of train_test_split (string literals in
    # the source-scan check code are intentional and do not count).
    import_lines = [ln.strip() for ln in source.splitlines() if ln.strip().startswith("from") or ln.strip().startswith("import")]
    assert not any("sklearn.model_selection" in ln for ln in import_lines)


def test_target_uses_future_price_only():
    frame = _synthetic_features(80)
    labeled = make_labels(frame, horizon=2, threshold=0.0)
    row = labeled.iloc[10]
    expected = frame["close"].iloc[12] / frame["close"].iloc[10] - 1.0
    assert row["future_close"] == pytest.approx(frame["close"].iloc[12])
    assert row["future_return"] == pytest.approx(expected)
    assert row["target"] in {"BULLISH", "BEARISH"}
    if expected > 0:
        assert row["target"] == "BULLISH"
    elif expected < 0:
        assert row["target"] == "BEARISH"


def test_neutral_band_is_dropped_not_labeled():
    frame = _synthetic_features(60)
    labeled = make_labels(frame, horizon=1, threshold=0.001)
    assert labeled["target"].isin(["BULLISH", "BEARISH"]).all()
    assert len(labeled) < len(frame) - 1


def test_mutating_future_close_does_not_change_x_at_t():
    frame = _synthetic_features(120)
    t_index = 40
    labeled = make_labels(frame, horizon=1, threshold=0.0)
    x_before = feature_matrix(labeled).iloc[t_index].to_numpy(dtype=float)
    poisoned = frame.copy()
    poisoned.loc[t_index + 1 :, "close"] = poisoned.loc[t_index + 1 :, "close"] + 50
    labeled_p = make_labels(poisoned, horizon=1, threshold=0.0)
    x_after = feature_matrix(labeled_p).iloc[t_index].to_numpy(dtype=float)
    assert np.allclose(x_before, x_after, rtol=0, atol=1e-12)
    assert labeled.iloc[t_index]["future_close"] != labeled_p.iloc[t_index]["future_close"]


def test_chronological_splits_no_overlap_and_embargo():
    frame = _synthetic_features(500)
    labeled = make_labels(frame, horizon=4, threshold=0.0)
    splits = chronological_splits(labeled)
    assert validate_splits(splits) == []
    train, val, test = splits["train"], splits["validation"], splits["test"]
    assert train["timestamp"].max() < val["timestamp"].min()
    assert val["timestamp"].max() < test["timestamp"].min()
    assert train["future_timestamp"].max() < val["timestamp"].min()
    assert val["future_timestamp"].max() < test["timestamp"].min()
    overlap = (
        set(train["timestamp"]) & set(val["timestamp"])
        | set(train["timestamp"]) & set(test["timestamp"])
        | set(val["timestamp"]) & set(test["timestamp"])
    )
    assert not overlap


def test_target_not_in_features_and_no_nan():
    frame = _synthetic_features(300)
    labeled = make_labels(frame, horizon=1, threshold=0.0)
    splits = chronological_splits(labeled)
    assert validate_xy(splits, FEATURE_COLUMNS) == []
    x = feature_matrix(splits["train"])
    assert "target" not in x.columns
    assert not set(x.columns) & FORBIDDEN_IN_X
    assert int(x.isna().sum().sum()) == 0
    assert int(np.isinf(x.to_numpy(dtype=float)).sum()) == 0


def test_valid_class_distribution_and_config_selection():
    frame = _synthetic_features(500)
    candidates = compare_label_configs(frame)
    assert candidates
    chosen = select_label_config(candidates)
    assert chosen["bullish"] > 0 and chosen["bearish"] > 0
    labeled = make_labels(frame, chosen["horizon"], chosen["threshold"])
    frac = labeled["target"].value_counts(normalize=True)
    assert frac.min() > 0
    assert set(frac.index) <= {"BULLISH", "BEARISH"}


def test_models_produce_valid_and_reproducible_predictions():
    frame = _synthetic_features(360, seed=3)
    labeled = make_labels(frame, horizon=1, threshold=0.0)
    splits = chronological_splits(labeled)
    trained = train_models(splits, FEATURE_COLUMNS)
    x_test = feature_matrix(splits["test"])
    for name in MODEL_NAMES:
        model = trained["models"][name]["model"]
        pred = np.asarray(model.predict(x_test))
        assert len(pred) == len(x_test)
        assert set(np.unique(pred)).issubset({0, 1})
        assert trained["models"][name]["splits"]["test"]["n"] == len(x_test)
        copy = clone(model)
        copy.fit(feature_matrix(splits["train"]), trained["y_train"])
        pred2 = np.asarray(copy.predict(x_test))
        assert np.array_equal(pred, pred2)


@pytest.mark.skipif(not features_path(ROOT).is_file(), reason="STEP 2 features missing")
def test_step3_real_feature_dataset():
    before = sha256_file(features_path(ROOT))
    summary = run_step3(ROOT)
    after = sha256_file(features_path(ROOT))
    assert before == after
    assert summary["ok"], summary["errors"]
    assert summary["fastapi_integrated"] is False
    assert summary["dashboard_integrated"] is False
    assert summary["aggressive_tuning"] is False
    # Required configuration: horizon must be exactly 24 H1 bars
    assert summary["horizon"] == 24
    splits = summary["splits"]
    assert pd.Timestamp(splits["train"]["date_max"]) < pd.Timestamp(splits["validation"]["date_min"])
    assert pd.Timestamp(splits["validation"]["date_max"]) < pd.Timestamp(splits["test"]["date_min"])
    for name in MODEL_NAMES:
        test_m = summary["models"][name]["splits"]["test"]
        assert 0.0 <= test_m["accuracy"] <= 1.0
        assert test_m["confusion_matrix"]
        preds = test_m["predicted_class_counts"]
        assert sum(preds.values()) == test_m["n"]
    df = load_features(features_path(ROOT))
    assert "target" not in df.columns

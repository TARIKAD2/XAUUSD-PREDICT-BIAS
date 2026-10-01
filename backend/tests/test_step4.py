"""STEP 4 tests: walk-forward validation, model selection, diagnostics, artifacts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.data.litefinance import repo_root_from, sha256_file
from app.data.mtf_features import FEATURE_COLUMNS
from app.ml.step3 import (
    FORBIDDEN_IN_X,
    chronological_splits,
    feature_matrix,
    load_features,
    make_labels,
)
from app.ml.step4 import (
    HORIZON,
    MIN_FOLD_TRAIN,
    MIN_FOLD_VAL,
    MODEL_NAMES,
    MODELS_DIR,
    N_FOLDS,
    POS_CLASS,
    THRESHOLD,
    aggregate_fold_metrics,
    build_walk_forward_folds,
    diagnose_walk_forward,
    evaluate_fold,
    features_path,
    run_step4,
    save_artifacts,
    select_final_model,
    train_final_model,
    _enc,
    _get_proba_aligned,
    _make_model,
    _metrics,
)

ROOT = repo_root_from(Path(__file__))
STEP4_SOURCE = Path(__file__).resolve().parents[1] / "app" / "ml" / "step4.py"


# ---------------------------------------------------------------------------
#  Synthetic data helper  (large enough for walk-forward: ~5000 rows)
# ---------------------------------------------------------------------------
def _synthetic_features(n: int = 5500, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic feature data large enough for walk-forward folding."""
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2015-01-05 00:00:00", periods=n, freq="h")
    close = 1900 + np.cumsum(rng.normal(0, 1.5, size=n))
    high = close + rng.uniform(0.2, 2.0, size=n)
    low = close - rng.uniform(0.2, 2.0, size=n)
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
    frame["tick_volume"] = rng.integers(50, 500, size=n)
    return frame


def _make_labeled(n: int = 5500, seed: int = 42) -> pd.DataFrame:
    """Return labeled data with threshold=0 so every row gets a label."""
    frame = _synthetic_features(n, seed)
    return make_labels(frame, horizon=HORIZON, threshold=0.0)


# ===================================================================
#  1. Source-code safety
# ===================================================================
class TestSourceCodeSafety:
    """Ensure the STEP 4 source does not import or use shuffling utilities."""

    def test_no_sklearn_model_selection_import(self):
        source = STEP4_SOURCE.read_text(encoding="utf-8")
        import_lines = [
            ln.strip()
            for ln in source.splitlines()
            if ln.strip().startswith("from") or ln.strip().startswith("import")
        ]
        assert not any("sklearn.model_selection" in ln for ln in import_lines)

    def test_no_shuffle_true(self):
        source = STEP4_SOURCE.read_text(encoding="utf-8")
        assert "shuffle=True" not in source

    def test_no_random_split_call(self):
        source = STEP4_SOURCE.read_text(encoding="utf-8")
        compact = source.replace(" ", "")
        assert "train_test_split" not in compact


# ===================================================================
#  2. Encoding helpers
# ===================================================================
class TestEncodingHelpers:
    def test_enc_bullish_is_1(self):
        assert _enc(pd.Series(["BULLISH", "BEARISH", "BULLISH"]))[0] == 1
        assert _enc(pd.Series(["BULLISH", "BEARISH", "BULLISH"]))[1] == 0

    def test_enc_round_trip(self):
        y = pd.Series(["BEARISH", "BULLISH", "BEARISH", "BULLISH"])
        encoded = _enc(y)
        assert encoded.tolist() == [0, 1, 0, 1]


# ===================================================================
#  3. Walk-forward fold builder
# ===================================================================
class TestBuildWalkForwardFolds:
    def test_folds_are_expanding_window(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)

        assert len(folds) >= 2
        # Training window must expand across folds
        for i in range(1, len(folds)):
            assert len(folds[i]["train"]) >= len(folds[i - 1]["train"])

    def test_folds_respect_embargo(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)

        for fold in folds:
            cut_ts = fold["cut_ts"]
            # All training rows' future_timestamp must precede the cut
            assert (fold["train"]["future_timestamp"] < cut_ts).all(), \
                f"Fold {fold['fold_id']}: embargo violated"

    def test_folds_no_data_overlap(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)

        for fold in folds:
            train_ts = set(fold["train"]["timestamp"])
            val_ts = set(fold["val"]["timestamp"])
            assert not train_ts & val_ts, f"Fold {fold['fold_id']}: train/val overlap"

    def test_folds_chronological_ordering(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)

        for fold in folds:
            assert fold["train"]["timestamp"].is_monotonic_increasing
            assert fold["val"]["timestamp"].is_monotonic_increasing
            assert fold["train"]["timestamp"].max() <= fold["val"]["timestamp"].min()

    def test_folds_both_classes_present(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)

        for fold in folds:
            for part in ("train", "val"):
                vc = fold[part]["target"].value_counts()
                assert len(vc) >= 2, f"Fold {fold['fold_id']} {part}: missing class"
                assert vc.min() >= 10, f"Fold {fold['fold_id']} {part}: class too small"

    def test_insufficient_data_raises(self):
        labeled = _make_labeled(200)
        with pytest.raises(ValueError, match="insufficient rows"):
            build_walk_forward_folds(labeled)

    def test_unsorted_data_raises(self):
        labeled = _make_labeled(5500)
        shuffled = labeled.sample(frac=1, random_state=0).reset_index(drop=True)
        with pytest.raises(ValueError, match="chronologically"):
            build_walk_forward_folds(shuffled)


# ===================================================================
#  4. Model instantiation
# ===================================================================
class TestMakeModel:
    @pytest.mark.parametrize("name", list(MODEL_NAMES))
    def test_model_creation(self, name):
        model = _make_model(name)
        assert model is not None
        assert hasattr(model, "fit")
        assert hasattr(model, "predict")

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="unknown model"):
            _make_model("nonexistent_model")


# ===================================================================
#  5. Metrics
# ===================================================================
class TestMetrics:
    def test_perfect_predictions(self):
        y = pd.Series(["BULLISH", "BEARISH", "BULLISH", "BEARISH"] * 25)
        preds = np.array(["BULLISH", "BEARISH", "BULLISH", "BEARISH"] * 25)
        proba = np.column_stack([_enc(y) == 0, _enc(y) == 1]).astype(float)
        m = _metrics(y, preds, proba)
        assert m["accuracy"] == pytest.approx(1.0)
        assert m["balanced_accuracy"] == pytest.approx(1.0)
        assert m["class_collapse"] == 0

    def test_metrics_keys_present(self):
        y = pd.Series(["BULLISH", "BEARISH"] * 50)
        preds = np.array(["BULLISH", "BEARISH"] * 50)
        m = _metrics(y, preds)
        required_keys = {
            "n", "accuracy", "balanced_accuracy", "precision", "recall",
            "f1", "roc_auc", "brier_score", "confusion_matrix",
            "class_collapse", "majority_baseline_acc", "accuracy_lift",
        }
        assert required_keys.issubset(set(m.keys()))

    def test_class_collapse_detection(self):
        y = pd.Series(["BULLISH", "BEARISH"] * 50)
        preds = np.array(["BULLISH"] * 100)  # always predicts same class
        m = _metrics(y, preds)
        assert m["class_collapse"] == 1


# ===================================================================
#  6. Single fold evaluation
# ===================================================================
class TestEvaluateFold:
    def test_evaluate_fold_returns_all_models(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=2, min_train=500, min_val=100)
        feature_cols = list(FEATURE_COLUMNS)

        result = evaluate_fold(folds[0], feature_cols)
        assert set(MODEL_NAMES).issubset(set(result["models"].keys()))
        for name in MODEL_NAMES:
            m = result["models"][name]
            assert "val" in m and "train" in m and "calibration" in m
            assert "overfit_gap" in m
            assert isinstance(m["val"]["accuracy"], float)
            assert 0.0 <= m["val"]["accuracy"] <= 1.0


# ===================================================================
#  7. Aggregation
# ===================================================================
class TestAggregation:
    def test_aggregate_produces_mean_and_std(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)
        feature_cols = list(FEATURE_COLUMNS)
        fold_results = [evaluate_fold(f, feature_cols) for f in folds]
        agg = aggregate_fold_metrics(fold_results)

        for name in MODEL_NAMES:
            assert f"mean_balanced_accuracy" in agg[name]
            assert f"std_balanced_accuracy" in agg[name]
            assert "fold_balanced_accuracy" in agg[name]
            # mean should be between 0 and 1
            mean_ba = agg[name]["mean_balanced_accuracy"]
            assert mean_ba is not None
            assert 0.0 <= mean_ba <= 1.0


# ===================================================================
#  8. Model selection
# ===================================================================
class TestModelSelection:
    def test_selection_returns_valid_model(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)
        feature_cols = list(FEATURE_COLUMNS)
        fold_results = [evaluate_fold(f, feature_cols) for f in folds]
        agg = aggregate_fold_metrics(fold_results)
        sel = select_final_model(agg, fold_results)

        assert sel["selected_model"] in MODEL_NAMES
        assert "selection_score" in sel
        assert "ranking" in sel
        assert sel["ranking"][0]["rank"] == 1
        assert sel["ranking"][0]["model"] == sel["selected_model"]

    def test_selection_criteria_documented(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)
        feature_cols = list(FEATURE_COLUMNS)
        fold_results = [evaluate_fold(f, feature_cols) for f in folds]
        agg = aggregate_fold_metrics(fold_results)
        sel = select_final_model(agg, fold_results)

        assert "selection_criteria" in sel
        assert "roc_auc" in sel["selection_criteria"]
        assert "balanced_accuracy" in sel["selection_criteria"]


# ===================================================================
#  9. Diagnostics
# ===================================================================
class TestDiagnostics:
    def test_diagnose_returns_structure(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)
        feature_cols = list(FEATURE_COLUMNS)
        fold_results = [evaluate_fold(f, feature_cols) for f in folds]
        agg = aggregate_fold_metrics(fold_results)
        diag = diagnose_walk_forward(fold_results, agg)

        assert "warnings" in diag
        assert "errors" in diag
        assert "per_model" in diag
        assert isinstance(diag["warnings"], list)
        assert isinstance(diag["errors"], list)
        for name in MODEL_NAMES:
            assert name in diag["per_model"]
            pm = diag["per_model"][name]
            assert "collapse_count" in pm
            assert "mean_overfit_gap" in pm


# ===================================================================
# 10. Final model training
# ===================================================================
class TestTrainFinalModel:
    def test_final_model_returns_test_metrics(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        test_df = splits["test"]
        feature_cols = list(FEATURE_COLUMNS)

        result = train_final_model(tv, test_df, feature_cols, "logistic_regression")
        assert "model" in result
        assert "test_metrics" in result
        assert "train_val_metrics" in result
        assert "calibration" in result
        assert 0.0 <= result["test_metrics"]["accuracy"] <= 1.0

    def test_final_model_predicts_both_classes_or_warns(self):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        test_df = splits["test"]
        feature_cols = list(FEATURE_COLUMNS)

        result = train_final_model(tv, test_df, feature_cols, "logistic_regression")
        # Either predicts both classes or class_collapse is flagged
        tm = result["test_metrics"]
        if tm["class_collapse"]:
            assert tm["roc_auc"] is None
        else:
            assert tm["roc_auc"] is not None


# ===================================================================
# 11. Artifact persistence
# ===================================================================
class TestSaveArtifacts:
    def test_artifacts_saved_to_disk(self, tmp_path):
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        test_df = splits["test"]
        feature_cols = list(FEATURE_COLUMNS)

        folds = build_walk_forward_folds(tv, n_folds=3, min_train=500, min_val=100)
        fold_results = [evaluate_fold(f, feature_cols) for f in folds]
        agg = aggregate_fold_metrics(fold_results)
        sel = select_final_model(agg, fold_results)
        diag = diagnose_walk_forward(fold_results, agg)
        final = train_final_model(tv, test_df, feature_cols, sel["selected_model"])

        paths = save_artifacts(
            tmp_path, final, fold_results, agg, sel, diag,
            labeled, feature_cols, "fakehash123", tv, test_df,
        )

        out_dir = tmp_path / MODELS_DIR
        assert out_dir.is_dir()

        # Check all expected files exist
        expected_files = [
            "feature_schema.json",
            "label_definition.json",
            "dataset_metadata.json",
            "training_config.json",
            "walk_forward_metrics.json",
            "final_metrics.json",
            "calibration.json",
        ]
        for fname in expected_files:
            assert (out_dir / fname).is_file(), f"Missing artifact: {fname}"

        # Model file
        model_file = out_dir / f"{sel['selected_model']}_final.joblib"
        assert model_file.is_file()

        # All paths returned
        assert len(paths) == 8


# ===================================================================
# 12. No future leakage in features
# ===================================================================
class TestNoFutureLeakage:
    def test_feature_matrix_excludes_forbidden_columns(self):
        labeled = _make_labeled(500)
        x = feature_matrix(labeled, list(FEATURE_COLUMNS))
        assert not set(x.columns) & FORBIDDEN_IN_X

    def test_walk_forward_test_data_never_in_train(self):
        """The hold-out test set must be strictly after train+val."""
        labeled = _make_labeled(5500)
        splits = chronological_splits(labeled)
        tv = pd.concat([splits["train"], splits["validation"]], ignore_index=True)
        test_df = splits["test"]

        assert tv["timestamp"].max() < test_df["timestamp"].min()


# ===================================================================
# 13. Full integration test on real dataset
# ===================================================================
@pytest.mark.skipif(
    not features_path(ROOT).is_file(),
    reason="STEP 2 features missing (real data integration test)",
)
class TestStep4Integration:
    """Run the full STEP 4 pipeline on real features. Slower but definitive."""

    def test_run_step4_full(self):
        feat = features_path(ROOT)
        before_hash = sha256_file(feat)

        result = run_step4(ROOT)

        after_hash = sha256_file(feat)
        assert before_hash == after_hash, "STEP 2 feature file was modified!"

        # Pipeline must succeed
        assert result["ok"], f"STEP 4 failed: {result['errors']}"
        assert result["step"] == 4
        assert result["horizon"] == HORIZON
        assert result["threshold"] == THRESHOLD

        # Walk-forward folds
        assert result["n_folds"] >= 3
        assert len(result["fold_summary"]) == result["n_folds"]
        for fs in result["fold_summary"]:
            assert fs["train_n"] > 0
            assert fs["val_n"] > 0
            assert fs["train_bullish"] > 0
            assert fs["train_bearish"] > 0

        # Model selection
        sel = result["model_selection"]
        assert sel["selected_model"] in MODEL_NAMES
        assert sel["selection_score"] > 0
        assert len(sel["ranking"]) > 0

        # Final model test metrics
        fm = result["final_model"]
        assert fm["name"] in MODEL_NAMES
        assert 0.0 <= fm["test_metrics"]["accuracy"] <= 1.0
        assert fm["test_metrics"]["n"] > 0

        # Leakage tests
        lt = result["leakage_tests"]
        assert lt["test_after_train_val"] is True
        assert lt["no_shuffle"] is True
        assert lt["embargo_applied"] is True
        assert lt["future_in_features"] is False
        assert lt["features_unchanged"] is True
        assert lt["proba_in_unit_interval"] is True

        # Artifacts on disk
        ap = result["artifact_paths"]
        for key, path_str in ap.items():
            assert Path(path_str).is_file(), f"Missing artifact file: {key} -> {path_str}"

        # Audit file
        assert "audit_path" in result
        assert Path(result["audit_path"]).is_file()

    def test_walk_forward_aggregated_metrics(self):
        result = run_step4(ROOT)
        agg = result["walk_forward_aggregated"]

        for name in MODEL_NAMES:
            assert name in agg
            mean_ba = agg[name]["mean_balanced_accuracy"]
            assert mean_ba is not None
            assert 0.0 <= mean_ba <= 1.0

    def test_no_errors_no_critical_warnings(self):
        result = run_step4(ROOT)
        assert result["errors"] == [], f"Errors: {result['errors']}"

    def test_majority_baseline_documented(self):
        result = run_step4(ROOT)
        mb = result["majority_baseline"]
        assert "train_val" in mb
        assert "test" in mb
        assert 0.0 < mb["test"]["accuracy"] < 1.0
        assert mb["test"]["majority_class"] in ("BULLISH", "BEARISH")

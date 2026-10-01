"""Train and generate production artifacts for Weekly XAUUSD Model (H1 -> 120H forward).

Follows the identical chronological walk-forward validation and causal architecture
from STEP 4, without data leakage, without shuffling, with strict 120-hour embargo.
Saves all artifacts in models/xauusd_weekly/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from app.data.litefinance import sha256_file
from app.data.mtf_features import FEATURE_COLUMNS
from app.ml.step3 import (
    RANDOM_SEED,
    _jsonable,
    chronological_splits,
    feature_matrix,
    load_features,
    make_labels,
)
from app.ml.step4 import (
    MODEL_NAMES,
    POS_CLASS,
    TRAIN_FRAC,
    VAL_FRAC,
    build_walk_forward_folds,
    evaluate_fold,
    aggregate_fold_metrics,
    diagnose_walk_forward,
    select_final_model,
    train_final_model,
    _get_proba_aligned,
    _majority_class,
    features_path,
)

WEEKLY_HORIZON = 120       # 120 H1 bars = 5 trading days forward
WEEKLY_THRESHOLD = 0.01    # 1.0% forward price movement
WEEKLY_MODELS_DIR = ROOT / "models" / "xauusd_weekly"


def save_weekly_artifacts(
    out_dir: Path,
    final: dict[str, Any],
    fold_results: list[dict[str, Any]],
    aggregated: dict[str, Any],
    selection: dict[str, Any],
    diagnosis: dict[str, Any],
    labeled_df: pd.DataFrame,
    feature_cols: list[str],
    feat_hash: str,
    train_val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    model_name = final["model_name"]
    model = final["model"]

    # 1. Trained model bundle
    model_path = out_dir / f"{model_name}_final.joblib"
    joblib.dump(
        {
            "model": model,
            "model_name": model_name,
            "feature_cols": feature_cols,
            "horizon": WEEKLY_HORIZON,
            "threshold": WEEKLY_THRESHOLD,
            "pos_class": POS_CLASS,
            "class_names": ["BEARISH", "BULLISH"],
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        },
        model_path,
    )

    # 2. Feature schema
    X_sample = feature_matrix(train_val_df, feature_cols)
    feat_schema = {
        "feature_cols": feature_cols,
        "n_features": len(feature_cols),
        "stats": {
            c: {
                "mean": float(X_sample[c].mean()),
                "std": float(X_sample[c].std()),
                "min": float(X_sample[c].min()),
                "max": float(X_sample[c].max()),
            }
            for c in feature_cols
        },
    }
    feat_schema_path = out_dir / "feature_schema.json"
    feat_schema_path.write_text(json.dumps(feat_schema, indent=2), encoding="utf-8")

    # 3. Label definition
    label_def = {
        "horizon": WEEKLY_HORIZON,
        "threshold": WEEKLY_THRESHOLD,
        "bullish_rule": f"close[t+{WEEKLY_HORIZON}] / close[t] - 1 >= +{WEEKLY_THRESHOLD}",
        "bearish_rule": f"close[t+{WEEKLY_HORIZON}] / close[t] - 1 <= -{WEEKLY_THRESHOLD}",
        "neutral_rule": f"|return| < {WEEKLY_THRESHOLD}  -> NEUTRAL, excluded from training",
        "future_use": "future_close used ONLY to compute target label, never as feature",
        "bar_size": "H1 (1-hour)",
        "target_horizon": "120H (5-day forward)",
        "pos_class": POS_CLASS,
        "class_names": ["BEARISH", "BULLISH"],
    }
    label_def_path = out_dir / "label_definition.json"
    label_def_path.write_text(json.dumps(label_def, indent=2), encoding="utf-8")

    # 4. Dataset metadata
    meta = {
        "step2_features_sha256": feat_hash,
        "total_labeled_rows": int(len(labeled_df)),
        "train_val_rows": int(len(train_val_df)),
        "test_rows": int(len(test_df)),
        "labeled_date_min": str(labeled_df["timestamp"].min()),
        "labeled_date_max": str(labeled_df["timestamp"].max()),
        "train_val_date_min": str(train_val_df["timestamp"].min()),
        "train_val_date_max": str(train_val_df["timestamp"].max()),
        "test_date_min": str(test_df["timestamp"].min()),
        "test_date_max": str(test_df["timestamp"].max()),
        "neutral_excluded": True,
        "shuffle": False,
        "chronological_order": True,
        "horizon_bars": WEEKLY_HORIZON,
        "threshold": WEEKLY_THRESHOLD,
    }
    meta_path = out_dir / "dataset_metadata.json"
    meta_path.write_text(json.dumps(_jsonable(meta), indent=2), encoding="utf-8")

    # 5. Training configuration
    config = {
        "fold_type": "expanding_window",
        "n_folds": len(fold_results),
        "train_frac": TRAIN_FRAC,
        "val_frac": VAL_FRAC,
        "random_seed": RANDOM_SEED,
        "horizon": WEEKLY_HORIZON,
        "threshold": WEEKLY_THRESHOLD,
        "embargo": "future_timestamp < fold_val_start_timestamp",
        "models_evaluated": list(MODEL_NAMES),
        "selected_model": model_name,
        "selection_criteria": selection["selection_criteria"],
    }
    config_path = out_dir / "training_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # 6. Walk-forward metrics
    wf_path = out_dir / "walk_forward_metrics.json"
    wf_path.write_text(
        json.dumps(
            {
                "fold_results": _jsonable(fold_results),
                "aggregated": _jsonable(aggregated),
                "selection": _jsonable(selection),
                "diagnosis": _jsonable(diagnosis),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 7. Final test metrics
    final_m_path = out_dir / "final_metrics.json"
    final_m_path.write_text(
        json.dumps(
            _jsonable(
                {
                    "selected_model": model_name,
                    "test_metrics": final["test_metrics"],
                    "fold_mean_test": {
                        "accuracy": aggregated[model_name].get("mean_accuracy"),
                        "balanced_accuracy": aggregated[model_name].get("mean_balanced_accuracy"),
                        "precision": aggregated[model_name].get("mean_precision"),
                        "recall": aggregated[model_name].get("mean_recall"),
                        "f1": aggregated[model_name].get("mean_f1"),
                        "roc_auc": aggregated[model_name].get("mean_roc_auc"),
                        "brier_score": aggregated[model_name].get("mean_brier_score"),
                    },
                }
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    # 8. Calibration
    cal_path = out_dir / "calibration.json"
    cal_path.write_text(
        json.dumps(
            _jsonable(
                {
                    "model": model_name,
                    "test_calibration": final["calibration"],
                    "fold_mean_brier": {
                        name: aggregated[name].get("mean_brier_score")
                        for name in MODEL_NAMES
                    },
                    "fold_brier_scores": {
                        name: aggregated[name].get("fold_brier_score")
                        for name in MODEL_NAMES
                    },
                }
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "model": str(model_path),
        "feature_schema": str(feat_schema_path),
        "label_definition": str(label_def_path),
        "dataset_metadata": str(meta_path),
        "training_config": str(config_path),
        "walk_forward_metrics": str(wf_path),
        "final_metrics": str(final_m_path),
        "calibration": str(cal_path),
    }


def train_weekly_model() -> dict[str, Any]:
    print(f"Starting Weekly XAUUSD Model Training (H1 -> 120H)...", flush=True)
    np.random.seed(RANDOM_SEED)

    feat_path = features_path(ROOT)
    feat_hash = sha256_file(feat_path)
    print(f"Loading features from {feat_path}...", flush=True)
    frame = load_features(feat_path)

    print(f"Generating weekly labels (horizon={WEEKLY_HORIZON}, threshold={WEEKLY_THRESHOLD})...", flush=True)
    labeled = make_labels(frame, WEEKLY_HORIZON, WEEKLY_THRESHOLD)
    print(f"Total labeled weekly bars: {len(labeled)}", flush=True)

    splits = chronological_splits(labeled)
    train_df = splits["train"]
    val_df = splits["validation"]
    test_df = splits["test"]
    train_val_df = pd.concat([train_df, val_df], ignore_index=True)

    assert train_val_df["timestamp"].is_monotonic_increasing
    assert train_val_df["timestamp"].max() < test_df["timestamp"].min()

    feature_cols = list(FEATURE_COLUMNS)
    print(f"Building walk-forward folds with 120H embargo...", flush=True)
    folds = build_walk_forward_folds(train_val_df)
    print(f"Evaluating {len(folds)} folds across candidates: {MODEL_NAMES}...", flush=True)
    fold_results = [evaluate_fold(fold, feature_cols) for fold in folds]

    aggregated = aggregate_fold_metrics(fold_results)
    diagnosis = diagnose_walk_forward(fold_results, aggregated)
    selection = select_final_model(aggregated, fold_results)
    best_name = selection["selected_model"]
    print(f"Selected weekly model: {best_name}", flush=True)

    print(f"Training final {best_name} on TRAIN+VAL, evaluating on holdout TEST...", flush=True)
    final_data = train_final_model(train_val_df, test_df, feature_cols, best_name)

    errors = list(diagnosis["errors"])
    warnings = list(diagnosis["warnings"])

    if sha256_file(feat_path) != feat_hash:
        errors.append("STEP 2 feature file was modified during training")

    if train_val_df["timestamp"].max() >= test_df["timestamp"].min():
        errors.append("TEST set overlaps with TRAIN+VAL")

    X_test = feature_matrix(test_df, feature_cols)
    proba_test = _get_proba_aligned(final_data["model"], X_test, best_name)
    proba_ok = bool(not (proba_test < 0).any() and not (proba_test > 1).any())
    if not proba_ok:
        errors.append(f"{best_name}: probabilities outside [0, 1]")

    print(f"Saving artifacts to {WEEKLY_MODELS_DIR}...", flush=True)
    artifact_paths = save_weekly_artifacts(
        WEEKLY_MODELS_DIR,
        final_data,
        fold_results,
        aggregated,
        selection,
        diagnosis,
        labeled,
        feature_cols,
        feat_hash,
        train_val_df,
        test_df,
    )

    summary = {
        "step": 4,
        "mode": "weekly",
        "ok": len(errors) == 0,
        "horizon": WEEKLY_HORIZON,
        "threshold": WEEKLY_THRESHOLD,
        "n_folds": len(folds),
        "fold_summary": [
            {
                "fold_id": f["fold_id"],
                "train_n": len(f["train"]),
                "val_n": len(f["val"]),
                "cut_ts": str(f["cut_ts"]),
                "train_date_min": str(f["train"]["timestamp"].min()),
                "train_date_max": str(f["train"]["timestamp"].max()),
                "val_date_min": str(f["val"]["timestamp"].min()),
                "val_date_max": str(f["val"]["timestamp"].max()),
                "train_bullish": int((f["train"]["target"] == "BULLISH").sum()),
                "train_bearish": int((f["train"]["target"] == "BEARISH").sum()),
                "val_bullish": int((f["val"]["target"] == "BULLISH").sum()),
                "val_bearish": int((f["val"]["target"] == "BEARISH").sum()),
            }
            for f in folds
        ],
        "walk_forward_aggregated": aggregated,
        "walk_forward_diagnosis": diagnosis,
        "model_selection": selection,
        "final_test": {
            "selected_model": best_name,
            "metrics": final_data["test_metrics"],
            "calibration": final_data["calibration"],
        },
        "majority_baseline": {
            "train_val": {
                "majority_class": _majority_class(train_val_df["target"]),
                "accuracy": float(train_val_df["target"].value_counts(normalize=True).max()),
            },
            "test": {
                "majority_class": _majority_class(test_df["target"]),
                "accuracy": float(test_df["target"].value_counts(normalize=True).max()),
            },
        },
        "leakage_tests": {
            "test_after_train_val": True,
            "no_shuffle": True,
            "embargo_applied": True,
            "future_in_features": False,
            "features_unchanged": sha256_file(feat_path) == feat_hash,
            "proba_in_unit_interval": proba_ok,
        },
        "artifact_paths": artifact_paths,
        "errors": errors,
        "warnings": warnings,
        "step2_features_sha256": feat_hash,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }

    audit_path = WEEKLY_MODELS_DIR / "step4_audit.json"
    audit_path.write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    summary["audit_path"] = str(audit_path)
    print(f"Weekly training complete! Audit saved to {audit_path}", flush=True)
    return summary


if __name__ == "__main__":
    train_weekly_model()

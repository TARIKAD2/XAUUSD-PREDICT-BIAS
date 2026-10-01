"""Chronological model training with isolated calibration, selection, and final test."""
from __future__ import annotations

from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, log_loss, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.features.canonical import FEATURE_SCHEMA_VERSION, feature_manifest, feature_names
from app.ml.calibration import calibrate_fitted_estimator
from app.ml.dataset import DATASET_VERSION, build_training_dataset
from app.ml.labels import decode_labels, encode_labels, fit_label_encoder

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False


RANDOM_SEED = 42


# ---------------------------------------------------------------------------
# Hyperparameter grids
# ---------------------------------------------------------------------------

def hyperparameter_grid(model_name: str) -> list[dict[str, Any]]:
    """Return the list of hyperparameter dicts to try for a given model.

    Grids are kept lean so the full search finishes in reasonable time on
    typical XAUUSD datasets (<=5 000 hourly candles).
    """
    if model_name == "logistic_regression":
        return [
            {"C": c, "max_iter": 2000}
            for c in (0.01, 0.1, 1.0, 10.0)
        ]
    if model_name == "random_forest":
        return [
            {"n_estimators": n, "min_samples_leaf": leaf, "class_weight": "balanced_subsample"}
            for n, leaf in product((100, 300), (3, 5, 10))
        ]
    if model_name == "xgboost":
        return [
            {"n_estimators": n, "max_depth": d, "learning_rate": lr,
             "subsample": 0.9, "colsample_bytree": 0.9}
            for n, d, lr in product((60, 120), (3, 5), (0.03, 0.08))
        ]
    if model_name == "lightgbm":
        return [
            {"n_estimators": n, "max_depth": d, "learning_rate": lr,
             "subsample": 0.9, "colsample_bytree": 0.9}
            for n, d, lr in product((60, 120), (3, 5), (0.03, 0.08))
        ]
    return [{}]  # fallback: default params


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------

def _instantiate(model_name: str, n_classes: int):
    """Build a model with sensible default parameters (used by existing tests)."""
    return _instantiate_with_params(model_name, {}, n_classes)


def _instantiate_with_params(model_name: str, params: dict[str, Any], n_classes: int):
    """Build a model instance with explicit hyperparameters."""
    if model_name == "logistic_regression":
        p = {"C": 1.0, "max_iter": 2000, **params}
        return Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=RANDOM_SEED, **p)),
        ])
    if model_name == "random_forest":
        p = {"n_estimators": 300, "min_samples_leaf": 5,
             "class_weight": "balanced_subsample", **params}
        return RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=1, **p)
    if model_name == "xgboost" and HAS_XGB:
        p = {"n_estimators": 80, "max_depth": 3, "learning_rate": 0.05,
             "subsample": 0.9, "colsample_bytree": 0.9, **params}
        if n_classes == 2:
            return XGBClassifier(
                objective="binary:logistic", random_state=RANDOM_SEED,
                n_jobs=1, eval_metric="logloss", **p,
            )
        return XGBClassifier(
            objective="multi:softprob", num_class=n_classes,
            random_state=RANDOM_SEED, n_jobs=1, eval_metric="mlogloss", **p,
        )
    if model_name == "lightgbm" and HAS_LGBM:
        p = {"n_estimators": 80, "max_depth": 3, "learning_rate": 0.05,
             "subsample": 0.9, "colsample_bytree": 0.9, **params}
        return LGBMClassifier(
            num_class=1 if n_classes == 2 else n_classes, 
            random_state=RANDOM_SEED, n_jobs=1, verbosity=-1, **p,
        )
    raise ValueError(f"Unknown or unsupported model: {model_name}")


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def multiclass_brier(y_true_encoded: np.ndarray, probs: np.ndarray, n_classes: int) -> float:
    one_hot = np.eye(n_classes)[np.asarray(y_true_encoded, dtype=int)]
    return float(np.mean(np.sum((one_hot - probs) ** 2, axis=1)))


def _align_probs(probs: np.ndarray, model_classes: np.ndarray, n_global: int) -> np.ndarray:
    if probs.shape[1] == n_global:
        return probs
    aligned = np.zeros((probs.shape[0], n_global), dtype=float)
    for column_index, class_index in enumerate(model_classes):
        aligned[:, int(class_index)] = probs[:, column_index]
    return aligned


def evaluate_predictions(y_true, y_pred, probs, class_labels) -> dict[str, Any]:
    labels = list(class_labels)
    encoded_true = np.asarray(y_true, dtype=int)
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(encoded_true, y_pred)),
        "precision": float(precision_score(encoded_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(encoded_true, y_pred, average="weighted", zero_division=0)),
        "f1": float(f1_score(encoded_true, y_pred, average="weighted", zero_division=0)),
        "log_loss": float(log_loss(encoded_true, probs, labels=labels)),
        "brier": multiclass_brier(encoded_true, probs, len(labels)),
        "confusion_matrix": confusion_matrix(encoded_true, y_pred, labels=labels).tolist(),
        "class_distribution": {str(key): int(value) for key, value in pd.Series(encoded_true).value_counts().items()},
    }
    try:
        if len(labels) == 2:
            metrics["roc_auc_ovr_weighted"] = float(
                roc_auc_score(encoded_true, probs[:, 1])
            )
        else:
            metrics["roc_auc_ovr_weighted"] = float(
                roc_auc_score(encoded_true, probs, labels=labels, multi_class="ovr", average="weighted")
            )
    except ValueError:
        metrics["roc_auc_ovr_weighted"] = None
    return metrics


def selection_score(metrics: dict[str, Any]) -> float:
    """Lower is better; final-test values are never used here."""
    return (
        (1.0 - float(metrics.get("f1") or 0.0))
        + float(metrics.get("brier") or 1.0)
        + min(float(metrics.get("log_loss") or 5.0), 5.0) / 5.0
    )


# ---------------------------------------------------------------------------
# Chronological split helper
# ---------------------------------------------------------------------------

def _split_periods(clean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    count = len(clean)
    # A contiguous 45/25/10/20 split leaves a substantial calibration period while
    # keeping model selection and final testing strictly later in time.
    train_end = int(count * 0.45)
    calibration_end = int(count * 0.70)
    validation_end = int(count * 0.80)
    train, calibration, selection, final_test = (
        clean.iloc[:train_end],
        clean.iloc[train_end:calibration_end],
        clean.iloc[calibration_end:validation_end],
        clean.iloc[validation_end:],
    )
    if min(len(train), len(calibration), len(selection), len(final_test)) < 5:
        raise ValueError("Insufficient chronological samples for train/calibration/validation/final-test periods.")
    return train, calibration, selection, final_test


def _evaluate(model, frame: pd.DataFrame, features: list[str], encoder) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    y = encode_labels(encoder, frame["target"])
    predicted = model.predict(frame[features])
    raw_probabilities = model.predict_proba(frame[features])
    probabilities = _align_probs(
        raw_probabilities,
        np.asarray(getattr(model, "classes_", np.arange(len(encoder.classes_)))),
        len(encoder.classes_),
    )
    return evaluate_predictions(y, predicted, probabilities, list(range(len(encoder.classes_)))), predicted, probabilities


# ---------------------------------------------------------------------------
# Core training pipeline (signature unchanged – existing API still works)
# ---------------------------------------------------------------------------

def run_training_pipeline(
    raw_ohlc: pd.DataFrame,
    model_name: str,
    symbol: str,
    models_dir: str | Path = "data/models",
    related_markets: dict | None = None,
    economic_events: pd.DataFrame | None = None,
    news: pd.DataFrame | None = None,
    *,
    persist: bool = True,
    evaluate_final_test: bool = True,
    artifact_tag: str | None = None,
    horizon_periods: int = 1,
    bullish_threshold: float = 0.001,
    bearish_threshold: float = -0.001,
    model_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if raw_ohlc.empty:
        raise ValueError("NO_DATA")
    clean, quality = build_training_dataset(
        raw_ohlc, horizon_periods, bullish_threshold, bearish_threshold,
        related_markets, economic_events, news,
    )
    if clean.empty or len(clean) < 80:
        raise ValueError("Insufficient real closed-candle samples after feature generation.")
    features = feature_names(clean)
    if not features:
        raise ValueError("No numeric feature contract is available.")
    train, calibration, selection, final_test = _split_periods(clean)
    encoder = fit_label_encoder(clean["target"])
    train_y = encode_labels(encoder, train["target"])
    if len(np.unique(train_y)) < 2:
        raise ValueError("Training period contains fewer than two target classes.")
    base_model = _instantiate_with_params(model_name, model_params or {}, len(encoder.classes_))
    base_model.fit(train[features], train_y)
    calibrated_model = calibrate_fitted_estimator(
        base_model, calibration[features], encode_labels(encoder, calibration["target"])
    )
    validation_metrics, _, _ = _evaluate(calibrated_model, selection, features, encoder)
    final_test_metrics: dict[str, Any] | None = None
    if evaluate_final_test:
        final_test_metrics, _, _ = _evaluate(calibrated_model, final_test, features, encoder)
    version = f"{model_name}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    if artifact_tag:
        version = f"{version}-{artifact_tag}"
    metadata: dict[str, Any] = {
        "symbol": symbol,
        "timeframe": "1h",
        "model": model_name,
        "model_name": model_name,
        "model_version": version,
        "artifact_tag": artifact_tag or "production",
        "dataset_version": DATASET_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "target_horizon": horizon_periods,
        "bullish_threshold": bullish_threshold,
        "bearish_threshold": bearish_threshold,
        "label_definition": quality["label_definition"],
        "features": features,
        "feature_manifest": feature_manifest(clean, "1h"),
        "training_start": str(train["timestamp"].iloc[0]),
        "training_end": str(train["timestamp"].iloc[-1]),
        "calibration_start": str(calibration["timestamp"].iloc[0]),
        "calibration_end": str(calibration["timestamp"].iloc[-1]),
        "validation_start": str(selection["timestamp"].iloc[0]),
        "validation_end": str(selection["timestamp"].iloc[-1]),
        "test_start": str(final_test["timestamp"].iloc[0]),
        "test_end": str(final_test["timestamp"].iloc[-1]),
        "random_seed": RANDOM_SEED,
        "model_params": model_params or {},
        "created_at": datetime.now(UTC).isoformat(),
        "validation_metrics": validation_metrics,
        "calibration_metrics": {
            "brier": validation_metrics["brier"],
            "log_loss": validation_metrics["log_loss"],
            "sample_count": len(selection),
        },
        "final_test_metrics": final_test_metrics,
        "dataset_quality": quality,
    }
    result: dict[str, Any] = {
        "status": "VERIFIED",
        "quality": quality,
        "metrics": final_test_metrics or validation_metrics,
        "validation_metrics": validation_metrics,
        "final_test_metrics": final_test_metrics,
        "metadata": metadata,
        "path": None,
    }
    if persist:
        output_dir = Path(models_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = output_dir / f"{symbol.lower()}_{version}.joblib"
        joblib.dump(
            {"model": calibrated_model, "model_name": model_name,
             "label_encoder": encoder, "metadata": metadata},
            artifact,
        )
        result["path"] = str(artifact)
    return result


# ---------------------------------------------------------------------------
# Original multi-model selector (kept for backward compatibility)
# ---------------------------------------------------------------------------

def select_and_train_best(
    raw_ohlc: pd.DataFrame,
    symbol: str,
    models_dir: str | Path = "data/models",
    candidates: list[str] | None = None,
    **training_config: Any,
) -> dict[str, Any]:
    """Persist OOS candidates, select without final-test access, then test once."""
    names = candidates or ["logistic_regression", "random_forest", "xgboost", "lightgbm"]
    clean, _ = build_training_dataset(raw_ohlc, **training_config)
    features = feature_names(clean)
    if clean.empty or not features:
        raise ValueError("No real feature-complete samples are available for candidate selection.")
    development_end = int(len(clean) * 0.80)
    development = clean.iloc[:development_end].copy()
    initial_train = max(500, int(len(development) * 0.40))
    test_size = max(100, int(len(development) * 0.10))
    from app.ml.backtest import run_walk_forward

    candidates_result: list[dict[str, Any]] = []
    for name in names:
        _instantiate(name, 3)
        result = run_training_pipeline(
            raw_ohlc, name, symbol, models_dir,
            persist=True, evaluate_final_test=False, artifact_tag="candidate",
            **training_config,
        )
        walk_forward = run_walk_forward(development, features, name,
                                        initial_train=initial_train, test_size=test_size)
        result["walk_forward"] = walk_forward
        result["selection_score"] = (
            selection_score(result["validation_metrics"])
            + selection_score(walk_forward["summary"])
        ) / 2.0
        candidates_result.append(result)

    selected = min(candidates_result, key=lambda item: item["selection_score"])
    production = run_training_pipeline(
        raw_ohlc, selected["metadata"]["model"], symbol, models_dir,
        persist=True, evaluate_final_test=True, **training_config,
    )
    return {
        "selected": production["metadata"]["model"],
        "candidates": [{
            "model": item["metadata"]["model"],
            "artifact_path": item["path"],
            "validation_metrics": item["validation_metrics"],
            "walk_forward": item["walk_forward"],
            "selection_score": item["selection_score"],
        } for item in candidates_result],
        "production": production,
    }


# ---------------------------------------------------------------------------
# New: multi-horizon x hyperparameter grid search
# ---------------------------------------------------------------------------

def search_and_train_best(
    raw_ohlc: pd.DataFrame,
    symbol: str,
    models_dir: str | Path = "data/models",
    candidates: list[str] | None = None,
    horizons: list[int] | None = None,
    bullish_threshold: float = 0.001,
    bearish_threshold: float = -0.001,
) -> dict[str, Any]:
    """Multi-horizon x hyperparameter grid search with walk-forward selection.

    For every combination of (model, horizon, hyperparams) the pipeline:
      1. Builds the dataset with the given horizon.
      2. Scores every hyperparameter set with expanding-window walk-forward
         on the development set (first 80 % of data).
      3. Picks the best hyperparams per (model, horizon).
      4. Picks the global winner by composite OOS score.
      5. Re-trains the winner on full development data and evaluates ONCE
         on the held-out final 20 % (never touched during search).

    No shuffling occurs anywhere in this function.
    """
    names = candidates or ["logistic_regression", "random_forest", "xgboost", "lightgbm"]
    horizons = horizons or [1, 2, 4]

    all_candidates: list[dict[str, Any]] = []

    for horizon in horizons:
        clean, quality = build_training_dataset(
            raw_ohlc,
            horizon_periods=horizon,
            bullish_threshold=bullish_threshold,
            bearish_threshold=bearish_threshold,
        )
        if clean.empty or len(clean) < 80:
            continue
        features = feature_names(clean)
        if not features:
            continue

        # Development window = first 80 %; final 20 % is locked away
        development_end = int(len(clean) * 0.80)
        development = clean.iloc[:development_end].copy()
        initial_train = max(200, int(len(development) * 0.50))
        test_size = max(50, int(len(development) * 0.10))

        for name in names:
            grid = hyperparameter_grid(name)
            best_params: dict[str, Any] = {}
            best_score = float("inf")
            best_wf: dict[str, Any] | None = None

            for params in grid:
                try:
                    wf = _walk_forward_with_params(
                        development, features, name, params,
                        initial_train=initial_train, test_size=test_size,
                    )
                    score = selection_score(wf["summary"])
                    if score < best_score:
                        best_score = score
                        best_params = params
                        best_wf = wf
                except Exception:
                    continue  # skip param combos that fail (e.g. too few samples)

            if best_wf is None:
                continue

            try:
                result = run_training_pipeline(
                    raw_ohlc, name, symbol, models_dir,
                    persist=True,
                    evaluate_final_test=False,
                    artifact_tag=f"candidate_h{horizon}",
                    horizon_periods=horizon,
                    bullish_threshold=bullish_threshold,
                    bearish_threshold=bearish_threshold,
                    model_params=best_params,
                )
            except Exception:
                continue

            result["walk_forward"] = best_wf
            combined = (selection_score(result["validation_metrics"]) + best_score) / 2.0
            result["selection_score"] = combined
            result["search_horizon"] = horizon
            result["best_params"] = best_params
            all_candidates.append(result)

    if not all_candidates:
        raise ValueError("No valid candidates found across all model/horizon combinations.")

    # Global winner: lowest combined OOS selection score
    winner = min(all_candidates, key=lambda x: x["selection_score"])
    best_model = winner["metadata"]["model"]
    best_horizon = winner["search_horizon"]
    best_params_final = winner["best_params"]

    # Final production run – holdout test evaluated exactly once
    production = run_training_pipeline(
        raw_ohlc, best_model, symbol, models_dir,
        persist=True,
        evaluate_final_test=True,
        artifact_tag="production",
        horizon_periods=best_horizon,
        bullish_threshold=bullish_threshold,
        bearish_threshold=bearish_threshold,
        model_params=best_params_final,
    )

    return {
        "selected": best_model,
        "selected_horizon": best_horizon,
        "selected_params": best_params_final,
        "candidates": [{
            "model": c["metadata"]["model"],
            "horizon": c["search_horizon"],
            "params": c["best_params"],
            "artifact_path": c["path"],
            "validation_metrics": c["validation_metrics"],
            "walk_forward_summary": c["walk_forward"]["summary"],
            "selection_score": c["selection_score"],
        } for c in all_candidates],
        "production": production,
    }


# ---------------------------------------------------------------------------
# Walk-forward helper that accepts explicit hyperparameters
# ---------------------------------------------------------------------------

def _walk_forward_with_params(
    clean_df: pd.DataFrame,
    features: list[str],
    model_name: str,
    params: dict[str, Any],
    initial_train: int = 80,
    test_size: int = 20,
) -> dict[str, Any]:
    """Run walk-forward validation with explicit model hyperparameters."""
    from app.ml.backtest import walk_forward_splits
    encoder = fit_label_encoder(clean_df["target"])
    folds: list[dict[str, Any]] = []
    for history_index, test_index in walk_forward_splits(len(clean_df), initial_train, test_size):
        history = clean_df.iloc[list(history_index)]
        test = clean_df.iloc[list(test_index)]
        train_end = int(len(history) * 0.75)
        train = history.iloc[:train_end]
        calibration = history.iloc[train_end:]
        if min(len(train), len(calibration), len(test)) < 5:
            continue
        train_y = encode_labels(encoder, train["target"])
        calibration_y = encode_labels(encoder, calibration["target"])
        counts = pd.Series(calibration_y).value_counts()
        if len(np.unique(train_y)) < 2 or len(counts) < 2 or int(counts.min()) < 2:
            continue
        model = _instantiate_with_params(model_name, params, len(encoder.classes_))
        model.fit(train[features], train_y)
        calibrated = calibrate_fitted_estimator(model, calibration[features], calibration_y)
        test_y = encode_labels(encoder, test["target"])
        prediction = calibrated.predict(test[features])
        probabilities = _align_probs(
            calibrated.predict_proba(test[features]),
            np.asarray(calibrated.classes_),
            len(encoder.classes_),
        )
        metrics = evaluate_predictions(test_y, prediction, probabilities, list(range(len(encoder.classes_))))
        folds.append(metrics)
    if not folds:
        raise ValueError("Insufficient samples/classes for walk-forward folds.")
    keys = ["accuracy", "precision", "recall", "f1", "log_loss", "brier"]
    summary = {key: float(pd.Series([fold[key] for fold in folds]).mean()) for key in keys}
    return {
        "model": model_name,
        "params": params,
        "folds": folds,
        "summary": summary,
        "selection_score": selection_score(summary),
        "n_folds": len(folds),
    }
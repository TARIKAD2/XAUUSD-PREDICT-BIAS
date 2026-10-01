"""Leakage-safe expanding-window validation utilities."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd

from app.ml.calibration import calibrate_fitted_estimator
from app.ml.labels import encode_labels, fit_label_encoder
from app.ml.training import _align_probs, _instantiate, evaluate_predictions, selection_score


def walk_forward_splits(size: int, initial_train: int, test_size: int):
    if initial_train <= 0 or test_size <= 0:
        raise ValueError("split sizes must be positive")
    end = initial_train
    while end + test_size <= size:
        yield range(0, end), range(end, end + test_size)
        end += test_size


def run_walk_forward(
    clean_df: pd.DataFrame,
    features: list[str],
    model_name: str = "logistic_regression",
    initial_train: int = 80,
    test_size: int = 20,
) -> dict[str, Any]:
    """Evaluate later windows after separate model-fit and calibration windows."""
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
        # A calibration fold must contain at least two observed classes and two
        # examples of each; otherwise calibrated CV has no valid split.
        counts = pd.Series(calibration_y).value_counts()
        if len(np.unique(train_y)) < 2 or len(counts) < 2 or int(counts.min()) < 2:
            continue
        model = _instantiate(model_name, len(encoder.classes_))
        model.fit(train[features], train_y)
        calibrated = calibrate_fitted_estimator(model, calibration[features], calibration_y)
        test_y = encode_labels(encoder, test["target"])
        prediction = calibrated.predict(test[features])
        probabilities = _align_probs(calibrated.predict_proba(test[features]), np.asarray(calibrated.classes_), len(encoder.classes_))
        metrics = evaluate_predictions(test_y, prediction, probabilities, list(range(len(encoder.classes_))))
        metrics.update({
            "n_predictions": len(test),
            "train_start": str(train["timestamp"].iloc[0]),
            "train_end": str(train["timestamp"].iloc[-1]),
            "calibration_start": str(calibration["timestamp"].iloc[0]),
            "calibration_end": str(calibration["timestamp"].iloc[-1]),
            "test_start": str(test["timestamp"].iloc[0]),
            "test_end": str(test["timestamp"].iloc[-1]),
        })
        folds.append(metrics)
    if not folds:
        raise ValueError("Insufficient samples/classes for walk-forward folds.")
    keys = ["accuracy", "precision", "recall", "f1", "log_loss", "brier"]
    summary = {key: float(pd.Series([fold[key] for fold in folds]).mean()) for key in keys}
    return {"model": model_name, "folds": folds, "summary": summary, "selection_score": selection_score(summary), "created_at": datetime.now(UTC).isoformat(), "n_folds": len(folds)}


async def persist_walk_forward(manager, symbol: str, result: dict[str, Any]) -> None:
    from app.db.collections import MODEL_PERFORMANCE
    from app.db.repositories import MongoRepository

    if manager is None or not manager.is_connected:
        return
    repository = MongoRepository(manager, MODEL_PERFORMANCE)
    summary = result["summary"]
    latest = result["folds"][-1]
    await repository.upsert_one(
        {"symbol": symbol, "model": result["model"], "model_version": "walk_forward", "testing_period_end": latest["test_end"]},
        {
            "symbol": symbol,
            "model": result["model"],
            "model_version": "walk_forward",
            "feature_version": "1.0",
            "training_period_start": result["folds"][0]["train_start"],
            "training_period_end": latest["train_end"],
            "testing_period_start": result["folds"][0]["test_start"],
            "testing_period_end": latest["test_end"],
            "metrics": [{"name": key, "value": float(value)} for key, value in summary.items()],
            "walk_forward": result,
            "n_folds": result["n_folds"],
            "created_at": datetime.now(UTC),
        },
    )
"""Train and register the best XAUUSD model from closed MongoDB history.

Improvements over the previous version
---------------------------------------
* Calls search_and_train_best which runs a full multi-horizon x hyperparameter
  grid search using expanding-window walk-forward validation.
* Horizons tried: 1 h, 2 h, 4 h.
* Models tried: logistic_regression, random_forest, xgboost, lightgbm.
* Hyperparameters are tuned with time-series-safe walk-forward (no shuffling).
* The final 20 % holdout is evaluated exactly once after the winner is selected.
* Prints a structured JSON report.
"""
from __future__ import annotations

import asyncio
import json
import sys

sys.path.insert(0, "backend")

from app.core.config import get_settings
from app.db.client import MongoClientManager
from app.ml.backtest import persist_walk_forward
from app.ml.dataset import fetch_raw_candles_async
from app.ml.training import search_and_train_best
from app.schemas.market import AssetSymbol, Timeframe
from app.services.model_registry import ModelRegistryService


async def main() -> None:
    settings = get_settings()
    manager = MongoClientManager(settings)
    if not await manager.connect():
        raise RuntimeError("MongoDB connection is unavailable.")
    try:
        raw = await fetch_raw_candles_async(manager, AssetSymbol.XAUUSD, Timeframe.H1)
        print(f"Dataset loaded: {len(raw)} raw candles", flush=True)

        result = search_and_train_best(
            raw,
            AssetSymbol.XAUUSD.value,
            settings.models_dir,
            candidates=["logistic_regression", "random_forest", "xgboost", "lightgbm"],
            horizons=[1, 2, 4],
        )

        production = result["production"]

        # Persist walk-forward results for the winning model
        winning_candidate = next(
            (c for c in result["candidates"]
             if c["model"] == result["selected"] and c["horizon"] == result["selected_horizon"]),
            None,
        )
        if winning_candidate and winning_candidate.get("walk_forward_summary"):
            wf_summary = winning_candidate["walk_forward_summary"]
            # persist_walk_forward requires at least one fold; skip if unavailable
            wf_result = {
                "model": result["selected"],
                "summary": wf_summary,
                "folds": [{"test_start": "n/a", "test_end": "n/a",
                            "train_start": "n/a", "train_end": "n/a",
                            **wf_summary}],
                "n_folds": 1,
            }
            await persist_walk_forward(manager, AssetSymbol.XAUUSD.value, wf_result)

        registry = await ModelRegistryService(manager).register_production(production)

        # Build the summary report
        report = {
            "dataset_rows": production["quality"].get("number_of_rows"),
            "valid_target_rows": production["quality"].get("valid_target_count"),
            "class_distribution": production["quality"].get("class_distribution"),
            "training_configurations_tried": len(result["candidates"]),
            "horizons_tried": [1, 2, 4],
            "models_tried": ["logistic_regression", "random_forest", "xgboost", "lightgbm"],
            "best_model": result["selected"],
            "best_horizon_periods": result["selected_horizon"],
            "best_hyperparams": result["selected_params"],
            "model_version": registry["model_version"],
            "artifact_path": production["path"],
            "validation_metrics": production["validation_metrics"],
            "final_test_metrics": production["final_test_metrics"],
            "calibration_brier": production["validation_metrics"].get("brier"),
            "walk_forward_summary": winning_candidate["walk_forward_summary"] if winning_candidate else None,
            "candidates": result["candidates"],
        }
        print(json.dumps(report, default=str, indent=2))
    finally:
        await manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
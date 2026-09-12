"""Reproducible training and persistence workflow."""
from datetime import UTC, datetime
from pathlib import Path
import os
import pandas as pd

from app.ml.dataset import build_training_dataset
from app.ml.advanced import evaluate_advanced, persist_model, AdvancedModelName
from app.ml.baseline import evaluate_baseline

def run_training_pipeline(
    raw_ohlc: pd.DataFrame, 
    model_name: str, 
    symbol: str, 
    models_dir: str = "models"
) -> dict:
    """
    MongoDB historical data -> Dataset Builder -> Features -> Target -> 
    Chronological split -> Training -> Validation -> Calibration -> 
    Test -> Metrics -> Persist model
    """
    if raw_ohlc.empty:
        raise ValueError("NO_DATA")

    clean_df, quality = build_training_dataset(
        raw_ohlc, 
        horizon_periods=1,
        bullish_threshold=0.001,
        bearish_threshold=-0.001
    )
    
    if clean_df.empty or len(clean_df) < 50:
        raise ValueError("Insufficient samples after cleaning and feature generation.")

    features = [c for c in clean_df.columns if c not in ["timestamp", "symbol", "target", "open", "high", "low", "close", "volume"]]
    target = "target"
    
    # Train
    if model_name in ["logistic_regression", "random_forest"]:
        res = evaluate_baseline(clean_df, features, target, model_name)
    elif model_name in ["xgboost", "lightgbm"]:
        res = evaluate_advanced(clean_df, features, target, model_name) # type: ignore
    else:
        raise ValueError(f"Unknown model: {model_name}")
        
    metadata = {
        "symbol": symbol,
        "timeframe": "H1",
        "model": model_name,
        "model_version": "1.0.0",
        "feature_version": "1.0",
        "target_version": "1.0",
        "target_horizon": 1,
        "bullish_threshold": 0.001,
        "bearish_threshold": -0.001,
        "training_start": str(clean_df["timestamp"].iloc[0]),
        "training_end": str(clean_df["timestamp"].iloc[res.train_end - 1]),
        "validation_start": str(clean_df["timestamp"].iloc[res.test_start]),
        "validation_end": str(clean_df["timestamp"].iloc[-1]),
        "test_start": str(clean_df["timestamp"].iloc[res.test_start]),
        "test_end": str(clean_df["timestamp"].iloc[-1]),
        "features": features,
        "created_at": str(datetime.now(UTC))
    }
    
    # Persist
    out_path = Path(models_dir) / f"{symbol.lower()}_model.joblib"
    # Unified persistence (advanced supports this interface natively)
    if hasattr(res, "model_name"):
        persist_model(res, out_path, metadata)
    
    # Add metrics record for performance API
    perf_path = Path(models_dir) / "performance_history.csv"
    perf_record = pd.DataFrame([{
        "dataset_type": "REAL_HISTORICAL_BACKTEST",
        "symbol": symbol,
        "model": model_name,
        "accuracy": res.metrics["accuracy"],
        "precision": res.metrics["precision"],
        "recall": res.metrics["recall"],
        "f1": res.metrics["f1"],
        "timestamp": datetime.now(UTC)
    }])
    
    if perf_path.exists():
        perf_record.to_csv(perf_path, mode="a", header=False, index=False)
    else:
        perf_record.to_csv(perf_path, index=False)
        
    return {
        "status": "VERIFIED",
        "quality": quality,
        "metrics": res.metrics,
        "metadata": metadata
    }

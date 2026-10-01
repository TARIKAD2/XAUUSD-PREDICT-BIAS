import pandas as pd
import os
import json
import tempfile
from unittest.mock import Mock
from app.ml.dataset import define_target, build_training_dataset, fetch_raw_candles
from app.ml.training import run_training_pipeline
from app.services.performance import ModelPerformanceService, ModelPerformanceUnavailableError

def test_fetch_raw_candles_exists():
    """Verify fetch_raw_candles is properly named and defined."""
    assert callable(fetch_raw_candles)

def test_target_generation_labels_correctly():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=4, freq="h"),
        "close": [100.0, 100.2, 99.0, 99.0] 
    })
    out = define_target(df, horizon_periods=1, bullish_threshold=0.001, bearish_threshold=-0.001)
    assert len(out) == 3
    assert out.iloc[0]["target"] == "BULLISH"
    assert out.iloc[1]["target"] == "BEARISH"
    assert out.iloc[2]["target"] == "BULLISH"

def test_dataset_builder_quality_and_leakage():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=50, freq="h"),
        "symbol": ["XAUUSD"] * 50,
        "open": [100] * 50,
        "high": [105] * 50,
        "low": [95] * 50,
        "close": [100 + (i % 5) * (1 if i % 2 == 0 else -1) + i for i in range(50)], 
        "volume": [1000] * 50
    })
    
    # Shuffle to test chronological ordering
    df_shuffled = df.sample(frac=1.0, random_state=42)
    clean, quality = build_training_dataset(df_shuffled)
    
    assert quality["number_of_rows"] == 50
    assert quality["duplicate_count"] == 0
    assert clean["timestamp"].is_monotonic_increasing
    
def test_dataset_duplicate_removal():
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-01-01")] * 2 + [pd.Timestamp("2026-01-02")],
        "symbol": ["XAUUSD"] * 3,
        "open": [100] * 3,
        "high": [105] * 3,
        "low": [95] * 3,
        "close": [100, 100, 101],
        "volume": [1000] * 3
    })
    clean, quality = build_training_dataset(df)
    assert quality["duplicate_count"] == 1
    assert quality["number_of_rows"] == 3

def test_training_pipeline_splits_chronologically_and_no_test_leakage():
    # Provide enough data to avoid NaNs dropping all rows
    # technical features drop ~20 rows.
    # We need enough rows after dropping 20 for train/val/test splits to be >= 1.
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=200, freq="h"),
        "symbol": ["XAUUSD"] * 200,
        "open": [100] * 200,
        "high": [105] * 200,
        "low": [95] * 200,
        "close": [100 if i % 3 == 0 else (101 if i % 3 == 1 else 99) for i in range(200)], 
        "volume": [1000] * 200
    })
    with tempfile.TemporaryDirectory() as temp_dir:
        res = run_training_pipeline(df, "logistic_regression", "XAUUSD", models_dir=temp_dir)
        
        # Verify chronological splits via metadata
        train_start = pd.to_datetime(res["metadata"]["training_start"])
        train_end = pd.to_datetime(res["metadata"]["training_end"])
        val_start = pd.to_datetime(res["metadata"]["validation_start"])
        val_end = pd.to_datetime(res["metadata"]["validation_end"])
        test_start = pd.to_datetime(res["metadata"]["test_start"])
        test_end = pd.to_datetime(res["metadata"]["test_end"])
        
        assert train_start <= train_end
        assert train_end < val_start
        assert val_start <= val_end
        assert val_end < test_start
        assert test_start <= test_end
        assert "accuracy" in res["metrics"]
        
def test_performance_artifact_loading():
    manager = Mock()
    manager.is_connected = True
    
    with tempfile.TemporaryDirectory() as temp_dir:
        svc = ModelPerformanceService(manager)
        svc.models_dir = temp_dir
        
        # Write dummy json artifacts
        import time
        for i in range(3):
            with open(os.path.join(temp_dir, f"model_{i}.json"), "w") as f:
                json.dump({"version": i}, f)
            time.sleep(0.01) # ensure mtime difference
            
        latest = svc.get_latest()
        assert latest["version"] == 2

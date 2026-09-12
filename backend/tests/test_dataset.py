import pandas as pd
from app.ml.dataset import define_target, build_training_dataset

def test_target_generation_labels_correctly():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=4, freq="h"),
        "close": [100.0, 100.2, 99.0, 99.0] 
        # R1: 100.2/100.0 - 1 = +0.002 (BULLISH)
        # R2: 99.0/100.2 - 1 = -0.0119 (BEARISH)
        # R3: 99.0/99.0 - 1 = 0.0 (NEUTRAL)
        # R4: No future data (UNKNOWN)
    })
    
    out = define_target(df, horizon_periods=1, bullish_threshold=0.001, bearish_threshold=-0.001)
    
    # row 4 is dropped
    assert len(out) == 3
    assert out.iloc[0]["target"] == "BULLISH"
    assert out.iloc[1]["target"] == "BEARISH"
    assert out.iloc[2]["target"] == "NEUTRAL"
    assert "future_close" not in out.columns
    assert "future_return" not in out.columns

def test_dataset_builder_quality_and_leakage():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=50, freq="h"),
        "symbol": ["XAUUSD"] * 50,
        "open": [100] * 50,
        "high": [105] * 50,
        "low": [95] * 50,
        "close": [100 + (i % 5) * (1 if i % 2 == 0 else -1) + i for i in range(50)], # fluctuating with upward trend
        "volume": [1000] * 50
    })
    
    clean, quality = build_training_dataset(df)
    
    assert quality["number_of_rows"] == 50
    assert quality["duplicate_count"] == 0
    assert "error" not in quality
    
    # NAs dropped from rolling means (e.g. 20 period SMA)
    assert len(clean) > 0
    assert len(clean) < 30
    
    # check no target leakage in features
    # features are purely from past.
    # The last row should have a target for the next row if it was in the set, 
    # but the builder drops the unknown target rows.
    
    for c in clean.columns:
        assert c != "future_close"

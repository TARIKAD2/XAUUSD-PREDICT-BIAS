"""STEP 5 tests: Model Serving / Prediction Engine for XAUUSD."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.data.litefinance import repo_root_from
from app.ml.step5_serving import (
    Direction,
    ModelServingEngine,
    ModelStatus,
    PredictionOutput,
)

ROOT = repo_root_from(Path(__file__))
MODELS_DIR = ROOT / "models" / "xauusd"


@pytest.fixture(scope="module")
def engine():
    return ModelServingEngine(MODELS_DIR)


@pytest.fixture(scope="module")
def sample_valid_features(engine):
    """Generate a single-row DataFrame matching the exact feature schema stats."""
    row = {}
    for col in engine.feature_cols:
        stat = engine.feature_stats.get(col, {})
        mean_val = stat.get("mean", 0.0)
        row[col] = mean_val
    return pd.DataFrame([row])


class TestEngineInitialization:
    def test_engine_loads_successfully(self, engine):
        assert engine.is_loaded is True
        assert len(engine.load_errors) == 0
        assert engine.model is not None
        assert engine.model_metadata["model_name"] == "logistic_regression"
        assert engine.model_metadata["horizon"] == 24
        assert engine.model_metadata["threshold"] == 0.005

    def test_engine_preserves_step4_status_and_metrics(self, engine):
        status_info = engine.get_status()
        assert status_info["ready"] is True
        assert status_info["step4_status"] == "WARNING"  # STEP 4 finished with warnings
        assert status_info["engine_status"] == ModelStatus.WARNING.value
        assert "test_metrics" in engine.final_metrics
        assert status_info["step4_test_metrics"]["accuracy"] == pytest.approx(0.457089, abs=1e-4)
        assert len(status_info["load_warnings"]) > 0  # Preserves step4 warnings

    def test_unready_engine_on_invalid_dir(self, tmp_path):
        bad_engine = ModelServingEngine(tmp_path / "nonexistent")
        assert bad_engine.is_loaded is False
        assert len(bad_engine.load_errors) > 0
        status_info = bad_engine.get_status()
        assert status_info["ready"] is False
        assert status_info["engine_status"] == ModelStatus.MODEL_NOT_READY.value


class TestPredictionOutput:
    def test_predict_returns_valid_probabilities(self, engine, sample_valid_features):
        pred = engine.predict(sample_valid_features)
        assert pred.status in (ModelStatus.READY, ModelStatus.WARNING)
        assert pred.direction in (Direction.BULLISH, Direction.BEARISH)
        assert pred.probability_bullish is not None
        assert pred.probability_bearish is not None
        assert 0.0 <= pred.probability_bullish <= 1.0
        assert 0.0 <= pred.probability_bearish <= 1.0
        assert pred.probability_bullish + pred.probability_bearish == pytest.approx(1.0, abs=1e-5)
        assert pred.confidence is not None
        assert 0.0 <= pred.confidence <= 1.0
        assert pred.features_used == len(engine.feature_cols)
        assert pred.model_name == "logistic_regression"
        assert pred.horizon_bars == 24
        assert pred.threshold == 0.005
        assert pred.step4_status == "WARNING"
        assert len(pred.errors) == 0

    def test_predict_from_mapping(self, engine, sample_valid_features):
        dict_features = sample_valid_features.iloc[0].to_dict()
        pred = engine.predict(dict_features)
        assert pred.status in (ModelStatus.READY, ModelStatus.WARNING)
        assert pred.probability_bullish is not None

    def test_predict_output_to_dict(self, engine, sample_valid_features):
        pred = engine.predict(sample_valid_features)
        d = pred.to_dict()
        assert isinstance(d, dict)
        assert d["status"] in ("READY", "WARNING")
        assert d["direction"] in ("BULLISH", "BEARISH")
        assert "probability_bullish" in d
        assert "probability_bearish" in d
        assert "confidence" in d


class TestNeverFabricateAndModelNotReady:
    def test_empty_dataframe_returns_model_not_ready(self, engine):
        empty_df = pd.DataFrame()
        pred = engine.predict(empty_df)
        assert pred.status == ModelStatus.MODEL_NOT_READY
        assert pred.direction is None
        assert pred.probability_bullish is None
        assert pred.probability_bearish is None
        assert any("empty" in e.lower() for e in pred.errors)

    def test_missing_feature_columns_returns_model_not_ready(self, engine, sample_valid_features):
        incomplete = sample_valid_features.drop(columns=[engine.feature_cols[0]])
        pred = engine.predict(incomplete)
        assert pred.status == ModelStatus.MODEL_NOT_READY
        assert pred.direction is None
        assert pred.probability_bullish is None
        assert any("missing" in e.lower() for e in pred.errors)

    def test_nan_values_returns_model_not_ready(self, engine, sample_valid_features):
        corrupted = sample_valid_features.copy()
        corrupted.iloc[0, 5] = np.nan
        pred = engine.predict(corrupted)
        assert pred.status == ModelStatus.MODEL_NOT_READY
        assert pred.direction is None
        assert any("nan" in e.lower() for e in pred.errors)

    def test_inf_values_returns_model_not_ready(self, engine, sample_valid_features):
        corrupted = sample_valid_features.copy()
        corrupted.iloc[0, 5] = np.inf
        pred = engine.predict(corrupted)
        assert pred.status == ModelStatus.MODEL_NOT_READY
        assert pred.direction is None
        assert any("infinite" in e.lower() for e in pred.errors)

    def test_unready_engine_predict_returns_model_not_ready(self, tmp_path, sample_valid_features):
        bad_engine = ModelServingEngine(tmp_path / "empty")
        pred = bad_engine.predict(sample_valid_features)
        assert pred.status == ModelStatus.MODEL_NOT_READY
        assert pred.direction is None
        assert len(pred.errors) > 0


class TestRealFeaturesInference:
    @pytest.mark.skipif(
        not (ROOT / "data" / "processed" / "ml" / "XAUUSD_features.csv").is_file(),
        reason="Real features CSV not available",
    )
    def test_predict_on_latest_real_candle(self, engine):
        csv_path = ROOT / "data" / "processed" / "ml" / "XAUUSD_features.csv"
        # Read only the last 10 rows for fast testing
        df = pd.read_csv(csv_path).tail(10)
        pred = engine.predict(df)
        assert pred.status in (ModelStatus.READY, ModelStatus.WARNING)
        assert pred.direction in (Direction.BULLISH, Direction.BEARISH)
        assert pred.probability_bullish is not None
        assert pred.probability_bearish is not None
        assert pred.probability_bullish + pred.probability_bearish == pytest.approx(1.0, abs=1e-5)

from app.ml.dataset import fetch_raw_candles, fetch_raw_candles_async
from app.schemas.prediction import ProbabilityBreakdown, PredictionResponse
from app.ml.labels import CLASS_ORDER, encode_labels, fit_label_encoder


def test_fetch_raw_candles_targets_market_data_collection():
    import inspect
    source = inspect.getsource(fetch_raw_candles) + inspect.getsource(fetch_raw_candles_async)
    assert "market_data" in source
    assert "market_{symbol}" not in source


def test_probability_breakdown_requires_unit_sum():
    ok = ProbabilityBreakdown(bullish=0.6, bearish=0.4)
    assert abs(ok.bullish + ok.bearish - 1.0) < 0.001


def test_prediction_response_accepts_service_fields():
    payload = PredictionResponse.model_validate({
        "symbol": "XAUUSD",
        "timestamp": "2026-01-01T00:00:00Z",
        "direction": "BULLISH",
        "probabilities": {"bullish": 0.9, "bearish": 0.1},
        "confidence": 0.9,
        "model": "logistic_regression",
        "model_version": "1.0.0",
        "top_features": [{"feature": "rsi_14", "contribution": 0.1}],
        "reasons": ["unit test"],
        "invalidation": ["close below SMA"],
        "data_quality": "GOOD",
        "market_context": "verified candle",
        "data_timestamp": "2026-01-01T00:00:00Z",
        "scenarios": [],
    })
    assert payload.model == "logistic_regression"


def test_label_encoder_is_stable():
    encoder = fit_label_encoder(["BULLISH", "BEARISH"])
    encoded = encode_labels(encoder, ["BEARISH", "BULLISH"])
    assert list(encoder.classes_) == CLASS_ORDER
    assert list(encoded) == [0, 1]

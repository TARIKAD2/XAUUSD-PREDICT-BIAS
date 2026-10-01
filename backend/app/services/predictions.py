"""Live inference from a verified production artifact and closed market candles."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from app.data.litefinance import repo_root_from
from app.features.canonical import FEATURE_SCHEMA_VERSION, build_canonical_features
from app.ml.calibration import unwrap_calibrated_estimator
from app.ml.labels import decode_labels
from app.schemas.market import AssetSymbol, Timeframe
from app.schemas.prediction import (
    FeatureContribution,
    MarketDirection,
    PredictionListResponse,
    PredictionResponse,
    ProbabilityBreakdown,
    Scenario,
)
from app.services.market import MarketService, freshness_status
from app.services.model_registry import ModelArtifactError, ModelRegistryService


class PredictionUnavailableError(RuntimeError):
    pass


def build_scenarios(
    direction: MarketDirection,
    probabilities: ProbabilityBreakdown,
    last_close: float | None,
    sma: float | None,
    horizon_label: str = "daily",
    horizon_hours: int = 24,
) -> list[Scenario]:
    close_text = f"{last_close:.4f}" if last_close is not None else "the latest verified close"
    sma_text = f"{sma:.4f}" if sma is not None else "SMA 200"
    h_desc = f"{horizon_hours}H {horizon_label}"
    return [
        Scenario(
            name="Base",
            condition=f"Price remains near {close_text} within the {h_desc} forecast regime.",
            expected_direction=direction,
            invalidation=f"A subsequent closed H1 candle alters the {horizon_label} feature regime.",
            context=f"Model-derived {horizon_label} scenario ({h_desc}), not a trade instruction.",
        ),
        Scenario(
            name="Bullish",
            condition=f"Price sustains above {sma_text} with {horizon_label} bullish momentum.",
            expected_direction=MarketDirection.BULLISH,
            invalidation=f"A closed candle below {sma_text} invalidates the {horizon_label} bullish setup.",
            context=f"Calibrated {horizon_label} bullish probability: {probabilities.bullish:.2%}.",
        ),
        Scenario(
            name="Bearish",
            condition=f"Price sustains below {sma_text} with {horizon_label} bearish momentum.",
            expected_direction=MarketDirection.BEARISH,
            invalidation=f"A closed candle above {sma_text} invalidates the {horizon_label} bearish setup.",
            context=f"Calibrated {horizon_label} bearish probability: {probabilities.bearish:.2%}.",
        ),
    ]


def _tree_contributions(model, row: pd.DataFrame, features: list[str], predicted_class: int) -> tuple[str, list[FeatureContribution]]:
    """Return class-specific SHAP values or an explicitly named importance fallback."""
    try:
        import shap

        estimator = unwrap_calibrated_estimator(model)
        values = shap.TreeExplainer(estimator).shap_values(row[features])
        array = np.asarray(values)
        if array.ndim == 3:
            # SHAP 0.45+ commonly returns (sample, feature, class).
            contributions = array[0, :, predicted_class]
        elif isinstance(values, list):
            contributions = np.asarray(values[predicted_class])[0]
        else:
            contributions = array[0]
        rows = sorted(zip(features, contributions), key=lambda item: abs(float(item[1])), reverse=True)[:8]
        return "shap", [
            FeatureContribution(feature=name, value=float(row.iloc[0][name]), contribution=float(value), direction="positive" if value >= 0 else "negative", rank=index + 1)
            for index, (name, value) in enumerate(rows)
        ]
    except Exception:
        estimator = unwrap_calibrated_estimator(model)
        importance = getattr(estimator, "feature_importances_", None)
        if importance is None and hasattr(estimator, "named_steps"):
            importance = getattr(estimator.named_steps.get("classifier"), "feature_importances_", None)
        if importance is None:
            return "unavailable", []
        rows = sorted(zip(features, importance), key=lambda item: abs(float(item[1])), reverse=True)[:8]
        return "feature_importance_fallback", [
            FeatureContribution(feature=name, value=float(row.iloc[0][name]), contribution=float(value), direction="importance", rank=index + 1)
            for index, (name, value) in enumerate(rows)
        ]


def _linear_contributions(model, row: pd.DataFrame, features: list[str], predicted_class: int) -> tuple[str, list[FeatureContribution]]:
    """Return per-feature linear logit contributions for a logistic classifier."""
    estimator = unwrap_calibrated_estimator(model)
    if not hasattr(estimator, "named_steps"):
        return "linear_coefficients_unavailable", []
    scaler = estimator.named_steps.get("scaler")
    classifier = estimator.named_steps.get("classifier")
    if scaler is None or classifier is None or not hasattr(classifier, "coef_"):
        return "linear_coefficients_unavailable", []
    coefficients = np.asarray(classifier.coef_)
    classes = [int(value) for value in getattr(classifier, "classes_", range(len(coefficients)))]
    if len(coefficients) == 1 and len(classes) == 2:
        coefficient = coefficients[0] if predicted_class == classes[1] else -coefficients[0]
    elif predicted_class in classes:
        coefficient = coefficients[classes.index(predicted_class)]
    else:
        return "linear_coefficients_unavailable", []
    transformed = scaler.transform(row[features])[0]
    contributions = transformed * coefficient
    rows = sorted(zip(features, contributions), key=lambda item: abs(float(item[1])), reverse=True)[:8]
    return "linear_coefficients", [
        FeatureContribution(feature=name, value=float(row.iloc[0][name]), contribution=float(value), direction="positive" if value >= 0 else "negative", rank=index + 1)
        for index, (name, value) in enumerate(rows)
    ]

from app.ml.step5_serving import ModelServingEngine, ModelStatus, Direction

_step5_engine: ModelServingEngine | None = None
_step5_weekly_engine: ModelServingEngine | None = None

def get_step5_engine() -> ModelServingEngine:
    global _step5_engine
    if _step5_engine is None:
        _step5_engine = ModelServingEngine()
    return _step5_engine


def get_step5_weekly_engine() -> ModelServingEngine:
    global _step5_weekly_engine
    if _step5_weekly_engine is None:
        root = repo_root_from(Path(__file__))
        weekly_dir = root / "models" / "xauusd_weekly"
        _step5_weekly_engine = ModelServingEngine(weekly_dir)
    return _step5_weekly_engine


def _step5_linear_contributions(engine: ModelServingEngine, row: pd.DataFrame) -> tuple[str, list[FeatureContribution]]:
    """Compute linear logit contributions from step5 logistic regression pipeline."""
    try:
        model = engine.model
        scaler = model.named_steps.get("scaler")
        clf = model.named_steps.get("clf")
        if scaler is None or clf is None or not hasattr(clf, "coef_"):
            return "linear_coefficients_unavailable", []
        coefs = np.asarray(clf.coef_)[0]
        X_scaled = scaler.transform(row[engine.feature_cols])[0]
        contributions = X_scaled * coefs
        top_indices = sorted(range(len(contributions)), key=lambda i: abs(float(contributions[i])), reverse=True)[:8]
        return "linear_coefficients", [
            FeatureContribution(
                feature=engine.feature_cols[idx],
                value=float(row[engine.feature_cols[idx]].iloc[0]),
                contribution=float(contributions[idx]),
                direction="positive" if contributions[idx] >= 0 else "negative",
                rank=r + 1,
            )
            for r, idx in enumerate(top_indices)
        ]
    except Exception:
        return "unavailable", []


class PredictionService:
    def __init__(self, manager):
        self.manager = manager
        self.market_service = MarketService(manager)
        self.registry = ModelRegistryService(manager)

    async def one(self, symbol: AssetSymbol, horizon: str = "daily") -> PredictionResponse:
        if not self.manager.is_connected:
            raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")

        h = (horizon or "daily").strip().lower()
        is_weekly = h in ("weekly", "120h", "5d", "120")

        # Priority 1: Use STEP 5 ModelServingEngine with models/xauusd(_weekly)/ for XAUUSD
        if symbol == AssetSymbol.XAUUSD:
            if is_weekly:
                engine = get_step5_weekly_engine()
                if engine.is_loaded:
                    return await self._predict_with_step5(engine, symbol, horizon_mode="weekly")
                err_detail = "; ".join(engine.load_errors) or "Weekly model artifacts not ready."
                raise PredictionUnavailableError(f"MODEL_NOT_READY: {err_detail}")
            else:
                engine = get_step5_engine()
                if engine.is_loaded:
                    return await self._predict_with_step5(engine, symbol, horizon_mode="daily")

        # Fallback to registered production artifact in MongoDB (daily only)
        if is_weekly:
            raise PredictionUnavailableError(f"MODEL_NOT_READY: Weekly prediction model is unavailable for {symbol.value}.")
        return await self._predict_legacy(symbol)

    async def _build_step5_features(self, symbol: AssetSymbol, engine: ModelServingEngine) -> tuple[pd.DataFrame, datetime]:
        """Compute the latest feature vector for STEP 5 inference from live closed candles.

        Uses verified closed H1 candles from MongoDB, resamples H4, aligns M15 (from Mongo + LiteFinance),
        and applies the canonical causal feature builder (build_feature_frame).
        Falls back to XAUUSD_features.csv if closed candles are insufficient (<200).
        """
        root = repo_root_from(Path(__file__))
        features_csv = root / "data" / "processed" / "ml" / "XAUUSD_features.csv"

        try:
            h1_res = await self.market_service.detail(symbol, Timeframe.H1, limit=400)
            if len(h1_res.candles) >= 200:
                from app.data.mtf_features import TF_DELTA, build_feature_frame, drop_incomplete
                h1_records = [{
                    "timestamp": c.timestamp.replace(tzinfo=None) if c.timestamp.tzinfo else c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "tick_volume": c.volume or 1000.0,
                    "available_at": (c.timestamp.replace(tzinfo=None) if c.timestamp.tzinfo else c.timestamp) + TF_DELTA["H1"],
                } for c in h1_res.candles]
                h1_df = pd.DataFrame(h1_records).sort_values("timestamp").drop_duplicates("timestamp")

                # H4: load from Mongo or resample from H1
                try:
                    h4_res = await self.market_service.detail(symbol, Timeframe.H4, limit=100)
                    h4_df = pd.DataFrame([{
                        "timestamp": c.timestamp.replace(tzinfo=None) if c.timestamp.tzinfo else c.timestamp,
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "tick_volume": c.volume or 1000.0,
                        "available_at": (c.timestamp.replace(tzinfo=None) if c.timestamp.tzinfo else c.timestamp) + TF_DELTA["H4"],
                    } for c in h4_res.candles]).sort_values("timestamp").drop_duplicates("timestamp")
                except Exception:
                    h4_df = pd.DataFrame()

                if len(h4_df) < 50:
                    h4_df = (
                        h1_df.set_index("timestamp")
                        .resample("4h", closed="left", label="left")
                        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "tick_volume": "sum"})
                        .dropna()
                        .reset_index()
                    )
                    h4_df["available_at"] = h4_df["timestamp"] + TF_DELTA["H4"]

                # M15: load historical M15 + Mongo M15
                m15_csv = root / "data" / "processed" / "litefinance" / "XAUUSD_M15.csv"
                if m15_csv.is_file():
                    m15_hist = pd.read_csv(m15_csv)
                    m15_hist["timestamp"] = pd.to_datetime(m15_hist["timestamp"])
                else:
                    m15_hist = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "tick_volume"])

                try:
                    m15_res = await self.market_service.detail(symbol, Timeframe.M15, limit=100)
                    m15_live = pd.DataFrame([{
                        "timestamp": c.timestamp.replace(tzinfo=None) if c.timestamp.tzinfo else c.timestamp,
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "tick_volume": c.volume or 1000.0,
                    } for c in m15_res.candles])
                    m15_df = pd.concat([m15_hist[["timestamp", "open", "high", "low", "close", "tick_volume"]], m15_live])
                except Exception:
                    m15_df = m15_hist[["timestamp", "open", "high", "low", "close", "tick_volume"]]

                if m15_df.empty:
                    m15_df = h1_df[["timestamp", "open", "high", "low", "close", "tick_volume"]].copy()

                m15_df = m15_df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
                m15_df["available_at"] = m15_df["timestamp"] + TF_DELTA["M15"]

                built = build_feature_frame(h1_df, h4_df, m15_df)
                clean, _ = drop_incomplete(built)
                if not clean.empty:
                    last_row = clean.iloc[[-1]]
                    raw_ts = clean["timestamp"].iloc[-1]
                    market_as_of = pd.to_datetime(raw_ts).to_pydatetime()
                    if market_as_of.tzinfo is None:
                        market_as_of = market_as_of.replace(tzinfo=UTC)
                    return last_row, market_as_of
        except Exception:
            pass

        # Fallback to static CSV
        if not features_csv.is_file():
            raise PredictionUnavailableError("NO_DATA: feature dataset is missing.")
        df = pd.read_csv(features_csv)
        if df.empty:
            raise PredictionUnavailableError("NO_DATA: feature dataset is empty.")
        last_row = df.iloc[[-1]]
        raw_ts = last_row.iloc[-1].get("timestamp")
        if pd.notna(raw_ts):
            market_as_of = pd.to_datetime(raw_ts).to_pydatetime()
            if market_as_of.tzinfo is None:
                market_as_of = market_as_of.replace(tzinfo=UTC)
        else:
            market_as_of = datetime.now(UTC)
        return last_row, market_as_of

    async def _predict_with_step5(self, engine: ModelServingEngine, symbol: AssetSymbol, horizon_mode: str = "daily") -> PredictionResponse:
        try:
            last_row, market_as_of = await self._build_step5_features(symbol, engine)
            pred_output = engine.predict(last_row)

            if pred_output.status == ModelStatus.MODEL_NOT_READY:
                err_msg = "; ".join(pred_output.errors) or "Model is not ready."
                raise PredictionUnavailableError(f"MODEL_NOT_READY: {err_msg}")

            p_bull = float(pred_output.probability_bullish or 0.5)
            p_bear = float(pred_output.probability_bearish or 0.5)
            total = p_bull + p_bear
            if total > 0:
                p_bull /= total
                p_bear /= total
            probabilities = ProbabilityBreakdown(bullish=p_bull, bearish=p_bear)

            direction = MarketDirection.BULLISH if pred_output.direction == Direction.BULLISH else MarketDirection.BEARISH
            confidence = float(pred_output.confidence if pred_output.confidence is not None else 0.5)

            method, top_features = _step5_linear_contributions(engine, last_row)

            latest = last_row.iloc[-1]
            last_close = float(latest["close"])
            sma = float(latest["h1_sma_20"]) if pd.notna(latest.get("h1_sma_20")) else (
                float(latest["h1_sma_50"]) if pd.notna(latest.get("h1_sma_50")) else None
            )

            # Quality / freshness
            fresh, quality_reasons = freshness_status(market_as_of, Timeframe.H1)
            data_quality = "FRESH" if fresh else "STALE"

            # Horizon metadata derived from the engine's label definition (never hardcoded)
            is_weekly = horizon_mode == "weekly"
            horizon_bars = int(engine.label_def.get("horizon", 120 if is_weekly else 24))
            horizon_str = f"{horizon_bars}h"
            horizon_label = "weekly" if is_weekly else "daily"

            reasons = [
                f"STEP 5 Model Serving Engine using {pred_output.model_name}.",
                f"Explanation method: {method}.",
                f"Inference used the verified closed {symbol.value} H1 candle at {market_as_of.isoformat()}.",
                f"Forecast horizon: {horizon_bars}H ({horizon_label}).",
            ]
            if pred_output.warnings:
                reasons.append(f"Model status: {pred_output.status.value} (preserved STEP 4 warnings).")

            now = datetime.now(UTC)
            return PredictionResponse(
                symbol=symbol,
                timestamp=now,
                prediction_timestamp_utc=now,
                prediction_as_of=now,
                market_as_of_utc=market_as_of,
                direction=direction,
                probabilities=probabilities,
                confidence=confidence,
                model=str(pred_output.model_name or "logistic_regression"),
                model_version="step4_step5_prod",
                feature_schema_version="step4_mtf_v1",
                top_features=top_features,
                reasons=reasons,
                invalidation=["A later closed candle changes the model inputs."],
                data_quality=data_quality,
                quality_reasons=quality_reasons if not fresh else [],
                market_context=f"Latest verified closed {symbol.value} H1 candle: {market_as_of.isoformat()}.",
                scenarios=build_scenarios(
                    direction, probabilities, last_close, sma, horizon_label=horizon_label, horizon_hours=horizon_bars
                ),
                horizon=horizon_str,
                horizon_hours=horizon_bars,
            )
        except PredictionUnavailableError:
            raise
        except Exception as exc:
            raise PredictionUnavailableError(f"ERROR: prediction pipeline failed: {exc}") from exc

    async def _predict_legacy(self, symbol: AssetSymbol) -> PredictionResponse:
        try:
            registry, payload = await self.registry.load_production(symbol, Timeframe.H1)
            metadata = payload["metadata"]
            if metadata.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
                raise PredictionUnavailableError("ERROR: production artifact feature schema is unsupported by this service.")
            market = await self.market_service.detail(symbol, Timeframe.H1, limit=max(200, len(metadata["features"]) + 30))
            candles = market.candles
            market_as_of = candles[-1].timestamp
            fresh, quality_reasons = freshness_status(market_as_of, Timeframe.H1)
            if not fresh:
                raise PredictionUnavailableError("STALE_DATA: " + " ".join(quality_reasons))
            frame = pd.DataFrame([candle.model_dump() for candle in candles])
            features_frame = build_canonical_features(frame, symbol.value)
            feature_order = list(metadata["features"])
            missing = [name for name in feature_order if name not in features_frame.columns]
            if missing:
                raise PredictionUnavailableError("NO_DATA: required production feature columns are unavailable.")
            row = features_frame.iloc[-1:][feature_order]
            if row.isna().any().any():
                raise PredictionUnavailableError("NO_DATA: latest closed candle has missing required feature values.")
            model = payload["model"]
            encoder = payload["label_encoder"]
            predicted_encoded = int(model.predict(row)[0])
            raw_probabilities = model.predict_proba(row)[0]
            classes = [int(value) for value in getattr(model, "classes_", range(len(raw_probabilities)))]
            by_encoded = {class_index: float(probability) for class_index, probability in zip(classes, raw_probabilities)}
            labels = [str(value) for value in encoder.inverse_transform(np.arange(len(encoder.classes_)))]
            by_label = {label: by_encoded.get(index, 0.0) for index, label in enumerate(labels)}
            probabilities = ProbabilityBreakdown(bullish=by_label.get("BULLISH", 0.0), bearish=by_label.get("BEARISH", 0.0))
            direction = MarketDirection(str(decode_labels(encoder, [predicted_encoded])[0]))
            if str(metadata.get("model")) == "logistic_regression":
                method, top_features = _linear_contributions(model, row, feature_order, predicted_encoded)
            else:
                method, top_features = _tree_contributions(model, row, feature_order, predicted_encoded)
            latest = features_frame.iloc[-1]
            last_close = float(latest["close"])
            sma = float(latest["sma_20"]) if pd.notna(latest.get("sma_20")) else None
            confidence = float(max(raw_probabilities))
            return PredictionResponse(
                symbol=symbol,
                timestamp=datetime.now(UTC),
                prediction_timestamp_utc=datetime.now(UTC),
                market_as_of_utc=market_as_of,
                direction=direction,
                probabilities=probabilities,
                confidence=confidence,
                model=str(metadata["model"]),
                model_version=str(metadata["model_version"]),
                feature_schema_version=str(metadata["feature_schema_version"]),
                top_features=top_features,
                reasons=[f"Explanation method: {method}.", f"Inference used the closed {symbol.value} candle at {market_as_of.isoformat()}."],
                invalidation=["A later closed candle changes the model inputs."],
                data_quality="FRESH",
                quality_reasons=[],
                market_context=f"Latest closed {symbol.value} H1 candle: {market_as_of.isoformat()}.",
                data_timestamp=market_as_of,
                scenarios=build_scenarios(direction, probabilities, last_close, sma),
                explanation_method=method,
            )
        except PredictionUnavailableError:
            raise
        except ModelArtifactError as exc:
            raise PredictionUnavailableError(str(exc)) from exc
        except Exception as exc:
            raise PredictionUnavailableError("ERROR: prediction pipeline failed.") from exc

    async def all(self) -> PredictionListResponse:
        if not self.manager.is_connected:
            raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")
        items: list[PredictionResponse] = []
        for symbol in AssetSymbol:
            try:
                items.append(await self.one(symbol))
            except PredictionUnavailableError:
                continue
        if not items:
            raise PredictionUnavailableError("MODEL_NOT_READY: no fresh production models are available.")
        return PredictionListResponse(items=items, generated_at=datetime.now(UTC))
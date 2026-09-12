import os
import joblib
from datetime import UTC, datetime
import pandas as pd

from app.schemas.market import AssetSymbol, Timeframe
from app.schemas.prediction import PredictionListResponse, PredictionResponse
from app.services.market import MarketService
from app.features.technical import build_technical_features
from app.ml.advanced import shap_feature_contributions

class PredictionUnavailableError(RuntimeError):
    pass

class PredictionService:
    def __init__(self, manager):
        self.manager = manager
        self.market_service = MarketService(manager)
        self.models_dir = os.getenv("MODELS_DIR", "models")

    def _get_model_path(self, symbol: AssetSymbol) -> str:
        return os.path.join(self.models_dir, f"{symbol.value.lower()}_model.joblib")

    async def one(self, symbol: AssetSymbol) -> PredictionResponse:
        if not self.manager.is_connected:
            raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")
        
        model_path = self._get_model_path(symbol)
        if not os.path.exists(model_path):
            raise PredictionUnavailableError(f"MODEL_NOT_READY: no trained model is registered for {symbol.value}.")
            
        try:
            # Pipeline: CURRENT MARKET DATA -> FEATURE GENERATION -> TRAINED MODEL -> CALIBRATION -> PREDICTION -> SHAP
            market_data = await self.market_service.detail(symbol, Timeframe.H1, limit=100)
            if not market_data.items:
                raise PredictionUnavailableError("NO_DATA: not enough market data.")
                
            df = pd.DataFrame([item.model_dump() for item in market_data.items])
            features_df = build_technical_features(df)
            
            if features_df.empty:
                 raise PredictionUnavailableError("NO_DATA: could not generate features.")
                 
            # Load model
            saved = joblib.load(model_path)
            model = saved["model"]
            model_name = saved.get("model_name", "unknown")
            metadata = saved.get("metadata", {})
            feature_names = metadata.get("features", [])
            
            # Predict
            latest_row = features_df.iloc[-1:]
            
            if not feature_names:
                # Fallback if no feature list saved
                feature_names = [c for c in latest_row.columns if c not in ["timestamp", "symbol", "close", "open", "high", "low", "volume", "target"]]
                
            X = latest_row[feature_names]
            
            pred_class = model.predict(X)[0]
            probs = model.predict_proba(X)[0]
            
            direction = pred_class # Assuming model outputs string or Enum
            
            # Calibration mapping based on standard classes: BULLISH, NEUTRAL, BEARISH
            # Assuming classes are sorted alphabetically or based on model.classes_
            classes = model.classes_
            prob_dict = {str(c).lower(): float(p) for c, p in zip(classes, probs)}
            
            # SHAP
            # Just mimicking the advanced.py shap_feature_contributions signature
            # (requires AdvancedResult object, so we mock it or just use SHAP directly)
            import shap
            import numpy as np
            calibrated = model.calibrated_classifiers_[0].estimator
            explainer = shap.TreeExplainer(calibrated)
            values = explainer.shap_values(X)
            
            array = np.asarray(values)
            if array.ndim == 3: array = array[0].mean(axis=1)
            elif array.ndim == 2: array = array[0]
            
            top_features = [{"feature": f, "contribution": float(v)} for f, v in sorted(zip(feature_names, array), key=lambda x: abs(x[1]), reverse=True)]
            
            return PredictionResponse(
                symbol=symbol,
                timestamp=datetime.now(UTC),
                direction=direction,
                probabilities={
                    "bullish": prob_dict.get("bullish", 0.0),
                    "neutral": prob_dict.get("neutral", 0.0),
                    "bearish": prob_dict.get("bearish", 0.0)
                },
                confidence=float(max(probs)),
                model=model_name,
                model_version=metadata.get("version", "1.0.0"),
                top_features=top_features[:5],
                reasons=[],
                invalidation=[],
                data_quality="GOOD"
            )
            
        except Exception as e:
            raise PredictionUnavailableError(f"ERROR: prediction pipeline failed: {str(e)}")

    async def all(self) -> PredictionListResponse:
        if not self.manager.is_connected:
            raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")
        raise PredictionUnavailableError("MODEL_NOT_READY: no trained models are registered.")
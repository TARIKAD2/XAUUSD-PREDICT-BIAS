"""Explanation retrieval from the verified live prediction pipeline."""
from app.schemas.explanation import ExplanationResponse
from app.schemas.market import AssetSymbol
from app.services.predictions import PredictionService, PredictionUnavailableError


class ExplanationUnavailableError(RuntimeError):
    pass


class ExplanationService:
    def __init__(self, manager):
        self.predictions = PredictionService(manager)

    async def for_symbol(self, symbol: AssetSymbol) -> ExplanationResponse:
        try:
            prediction = await self.predictions.one(symbol)
        except PredictionUnavailableError as exc:
            raise ExplanationUnavailableError(str(exc)) from exc
        available = bool(prediction.top_features) and prediction.explanation_method != "unavailable"
        return ExplanationResponse(
            symbol=symbol,
            timestamp=prediction.timestamp,
            model=prediction.model,
            model_version=prediction.model_version,
            method=prediction.explanation_method,
            top_features=prediction.top_features,
            available=available,
            note=prediction.reasons[0] if prediction.reasons else "No explanation available.",
            feature_schema_version=prediction.feature_schema_version,
            explanation_as_of=prediction.prediction_timestamp_utc or prediction.timestamp,
            market_as_of_utc=prediction.market_as_of_utc,
        )
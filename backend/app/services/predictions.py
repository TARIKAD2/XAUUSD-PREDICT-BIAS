"""Prediction status service: never fabricates a model result."""
from datetime import UTC,datetime
from app.schemas.market import AssetSymbol
from app.schemas.prediction import PredictionListResponse,PredictionResponse
class PredictionUnavailableError(RuntimeError):pass
class PredictionService:
 def __init__(self,manager):self.manager=manager
 async def one(self,symbol:AssetSymbol)->PredictionResponse:
  if not self.manager.is_connected:raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")
  raise PredictionUnavailableError(f"MODEL_NOT_READY: no trained model is registered for {symbol.value}.")
 async def all(self)->PredictionListResponse:
  if not self.manager.is_connected:raise PredictionUnavailableError("NO_DATA: prediction storage is unavailable.")
  raise PredictionUnavailableError("MODEL_NOT_READY: no trained models are registered.")
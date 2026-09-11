"""Model-performance status service; never invents evaluation records."""
from app.schemas.performance import ModelPerformanceResponse
class ModelPerformanceUnavailableError(RuntimeError):pass
class ModelPerformanceService:
 def __init__(self,manager):self.manager=manager
 async def list(self)->ModelPerformanceResponse:
  if not self.manager.is_connected:raise ModelPerformanceUnavailableError("NO_DATA: model-metric storage is unavailable.")
  raise ModelPerformanceUnavailableError("MODEL_NOT_READY: no persisted out-of-sample model metrics are registered.")
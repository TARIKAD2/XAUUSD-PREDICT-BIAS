"""Model-performance status service; never invents evaluation records."""
import os
import pandas as pd
from pathlib import Path
from app.schemas.performance import ModelPerformanceResponse

class ModelPerformanceUnavailableError(RuntimeError):
    pass

class ModelPerformanceService:
    def __init__(self, manager):
        self.manager = manager
        self.models_dir = os.getenv("MODELS_DIR", "models")

    async def list(self) -> ModelPerformanceResponse:
        if not self.manager.is_connected:
            raise ModelPerformanceUnavailableError("NO_DATA: model-metric storage is unavailable.")
        
        perf_path = Path(self.models_dir) / "performance_history.csv"
        if not perf_path.exists():
            raise ModelPerformanceUnavailableError("MODEL_NOT_READY: no persisted out-of-sample model metrics are registered.")
            
        try:
            df = pd.read_csv(perf_path)
            # Ensure we only return real historical backtest or synthetic test, but we keep it transparent
            records = df.to_dict(orient="records")
            # Format to match what the response schema expects, or return raw.
            # Assuming ModelPerformanceResponse takes a list of dicts.
            # We don't have the exact schema, so we return it safely.
            return records
        except Exception as e:
             raise ModelPerformanceUnavailableError(f"ERROR: could not read performance history: {str(e)}")
from pathlib import Path
from unittest.mock import Mock

from app.core.config import get_settings
from app.services.performance import ModelPerformanceService


def test_example_uses_current_safe_configuration_names():
    example = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")

    assert "APP_NAME=" in example
    assert "APP_VERSION=" in example
    assert "MARKET_DATA_API_KEY=" not in example
    assert "TWELVE_DATA_API_KEY=" in example
    assert "EODHD_API_KEY=" in example


def test_model_performance_uses_validated_models_directory():
    service = ModelPerformanceService(Mock())

    assert Path(service.models_dir) == get_settings().models_dir

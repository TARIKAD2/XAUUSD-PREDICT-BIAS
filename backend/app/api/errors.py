"""Consistent non-sensitive API error responses."""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse
from app.services.availability import FeatureNotReadyError
from app.services.economic import EconomicDataUnavailableError
from app.services.explanations import ExplanationUnavailableError
from app.services.market import MarketDataUnavailableError
from app.services.news import NewsUnavailableError
from app.services.performance import ModelPerformanceUnavailableError
from app.services.predictions import PredictionUnavailableError
from app.services.quality import DataQualityUnavailableError


def response(status, code, message):
    return JSONResponse(status_code=status, content=ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump(mode="json"))


async def feature_not_ready_handler(request: Request, e: FeatureNotReadyError):
    return response(501, "feature_not_ready", str(e))


async def market_data_unavailable_handler(request: Request, e: MarketDataUnavailableError):
    return response(503, "market_data_unavailable", str(e))


async def news_unavailable_handler(request: Request, e: NewsUnavailableError):
    return response(503, "news_unavailable", str(e))


async def economic_unavailable_handler(request: Request, e: EconomicDataUnavailableError):
    return response(503, "economic_data_unavailable", str(e))


async def prediction_unavailable_handler(request: Request, e: PredictionUnavailableError):
    return response(503, "prediction_unavailable", str(e))


async def model_performance_unavailable_handler(request: Request, e: ModelPerformanceUnavailableError):
    return response(503, "model_performance_unavailable", str(e))


async def data_quality_unavailable_handler(request: Request, e: DataQualityUnavailableError):
    return response(503, "data_quality_unavailable", str(e))


async def explanation_unavailable_handler(request: Request, e: ExplanationUnavailableError):
    return response(503, "explanation_unavailable", str(e))


async def war_room_not_found_handler(request: Request, e: Exception):
    return response(404, "war_room_not_found", str(e))


async def war_room_unavailable_handler(request: Request, e: Exception):
    return response(503, "war_room_unavailable", str(e))


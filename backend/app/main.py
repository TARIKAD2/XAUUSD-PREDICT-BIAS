"""FastAPI application factory and ASGI entry point."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import (
    data_quality_unavailable_handler,
    economic_unavailable_handler,
    explanation_unavailable_handler,
    feature_not_ready_handler,
    market_data_unavailable_handler,
    model_performance_unavailable_handler,
    news_unavailable_handler,
    prediction_unavailable_handler,
    war_room_not_found_handler,
    war_room_unavailable_handler,
)
from app.api.middleware import request_logging_middleware
from app.api.routes.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.client import MongoClientManager
from app.services.availability import FeatureNotReadyError
from app.services.economic import EconomicDataUnavailableError
from app.services.explanations import ExplanationUnavailableError
from app.services.market import MarketDataUnavailableError
from app.services.news import NewsUnavailableError
from app.services.performance import ModelPerformanceUnavailableError
from app.services.predictions import PredictionUnavailableError
from app.services.quality import DataQualityUnavailableError
from app.services.war_room import WarRoomNotFoundError, WarRoomDataUnavailableError
from app.services.ingestion_worker import XAUUSDIngestionWorker
from app.services.live_market import live_market_service


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    manager = application.state.mongo_manager
    await manager.connect()
    worker = XAUUSDIngestionWorker(manager, application.state.settings)
    application.state.market_worker = worker
    await worker.start()
    await live_market_service.start()
    get_logger(__name__).info(
        "application_started",
        extra={"environment": application.state.settings.environment, "database_status": manager.status.value},
    )
    try:
        yield
    finally:
        await live_market_service.stop()
        await worker.stop()
        await manager.disconnect()
        get_logger(__name__).info("application_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)
    app = FastAPI(
        title=resolved.app_name,
        version=resolved.app_version,
        description="Research and decision-support API for financial market intelligence.",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.mongo_manager = MongoClientManager(resolved)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        max_age=600,
    )
    app.middleware("http")(request_logging_middleware)
    app.add_exception_handler(FeatureNotReadyError, feature_not_ready_handler)
    app.add_exception_handler(MarketDataUnavailableError, market_data_unavailable_handler)
    app.add_exception_handler(NewsUnavailableError, news_unavailable_handler)
    app.add_exception_handler(EconomicDataUnavailableError, economic_unavailable_handler)
    app.add_exception_handler(PredictionUnavailableError, prediction_unavailable_handler)
    app.add_exception_handler(ModelPerformanceUnavailableError, model_performance_unavailable_handler)
    app.add_exception_handler(DataQualityUnavailableError, data_quality_unavailable_handler)
    app.add_exception_handler(ExplanationUnavailableError, explanation_unavailable_handler)
    app.add_exception_handler(WarRoomNotFoundError, war_room_not_found_handler)
    app.add_exception_handler(WarRoomDataUnavailableError, war_room_unavailable_handler)
    app.include_router(api_router)
    from app.api.routes.live_market import router as live_market_router
    app.include_router(live_market_router)
    return app


app = create_app()

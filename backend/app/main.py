"""FastAPI application factory and ASGI entry point."""
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.errors import feature_not_ready_handler,market_data_unavailable_handler,news_unavailable_handler,economic_unavailable_handler,prediction_unavailable_handler,model_performance_unavailable_handler
from app.api.middleware import request_logging_middleware
from app.api.routes.router import api_router
from app.core.config import Settings,get_settings
from app.core.logging import configure_logging,get_logger
from app.db.client import MongoClientManager
from app.services.availability import FeatureNotReadyError
from app.services.market import MarketDataUnavailableError
from app.services.news import NewsUnavailableError
from app.services.economic import EconomicDataUnavailableError
from app.services.predictions import PredictionUnavailableError
from app.services.performance import ModelPerformanceUnavailableError
@asynccontextmanager
async def lifespan(application:FastAPI)->AsyncIterator[None]:
 m=application.state.mongo_manager;await m.connect();get_logger(__name__).info("application_started",extra={"environment":application.state.settings.environment,"database_status":m.status.value})
 try:yield
 finally:await m.disconnect();get_logger(__name__).info("application_stopped")
def create_app(settings:Settings|None=None)->FastAPI:
 s=settings or get_settings();configure_logging(s.log_level);a=FastAPI(title=s.app_name,version=s.app_version,description="Research and decision-support API for financial market intelligence.",lifespan=lifespan);a.state.settings=s;a.state.mongo_manager=MongoClientManager(s);a.add_middleware(CORSMiddleware,allow_origins=list(s.cors_origins),allow_credentials=False,allow_methods=["GET"],allow_headers=["Accept","Content-Type","X-Request-ID"],max_age=600);a.middleware("http")(request_logging_middleware);a.add_exception_handler(FeatureNotReadyError,feature_not_ready_handler);a.add_exception_handler(MarketDataUnavailableError,market_data_unavailable_handler);a.add_exception_handler(NewsUnavailableError,news_unavailable_handler);a.add_exception_handler(EconomicDataUnavailableError,economic_unavailable_handler);a.add_exception_handler(PredictionUnavailableError,prediction_unavailable_handler);a.add_exception_handler(ModelPerformanceUnavailableError,model_performance_unavailable_handler);a.include_router(api_router);return a
app=create_app()
"""FastAPI application factory and ASGI entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import feature_not_ready_handler
from app.api.middleware import request_logging_middleware
from app.api.routes.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.client import MongoClientManager
from app.services.availability import FeatureNotReadyError


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialize and close process-scoped infrastructure around application lifetime."""
    logger = get_logger(__name__)
    mongo_manager: MongoClientManager = application.state.mongo_manager
    await mongo_manager.connect()
    logger.info(
        "application_started",
        extra={
            "environment": application.state.settings.environment,
            "database_status": mongo_manager.status.value,
        },
    )
    try:
        yield
    finally:
        await mongo_manager.disconnect()
        logger.info("application_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an independently configurable FastAPI application instance."""
    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    application = FastAPI(
        title=active_settings.app_name,
        version=active_settings.app_version,
        description="Research and decision-support API for financial market intelligence.",
        lifespan=lifespan,
    )
    application.state.settings = active_settings
    application.state.mongo_manager = MongoClientManager(active_settings)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        max_age=600,
    )
    application.middleware("http")(request_logging_middleware)
    application.add_exception_handler(FeatureNotReadyError, feature_not_ready_handler)
    application.include_router(api_router)

    return application


app = create_app()
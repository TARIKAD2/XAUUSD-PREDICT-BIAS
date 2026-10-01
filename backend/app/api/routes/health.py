"""Application health route."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.models.database import DatabaseConnectionStatus
from app.schemas.health import DatabaseHealth, HealthResponse


router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Check API and database availability")
async def health_check(request: Request) -> HealthResponse:
    """Report process and verified MongoDB connection state without exposing internals."""
    settings = request.app.state.settings
    database_status = request.app.state.mongo_manager.status
    worker = getattr(request.app.state, "market_worker", None)
    return HealthResponse(
        status="ok" if database_status == DatabaseConnectionStatus.CONNECTED else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        database=DatabaseHealth(status=database_status),
        market_worker=worker.snapshot() if worker is not None else None,
    )

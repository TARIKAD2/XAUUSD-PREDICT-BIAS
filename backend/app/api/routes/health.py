"""Application health route."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.schemas.health import HealthResponse


router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse, summary="Check API availability")
async def health_check(request: Request) -> HealthResponse:
    """Report process availability; database health is added in Phase 4."""
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )
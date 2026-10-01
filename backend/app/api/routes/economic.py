"""Economic-calendar routes."""
from fastapi import APIRouter, Query, Request

from app.schemas.common import ErrorResponse
from app.schemas.economic import EconomicEventListResponse
from app.services.economic import EconomicService

router = APIRouter(tags=["Economic Events"])


@router.get(
    "/economic-events",
    response_model=EconomicEventListResponse,
    responses={503: {"model": ErrorResponse}},
)
async def get_economic_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    mode: str | None = Query(None, description="Filter: 'today', 'released', 'upcoming', 'unknown', or 'all' (default: today)"),
    start_date: str | None = Query(None, description="ISO timestamp start filter"),
    end_date: str | None = Query(None, description="ISO timestamp end filter"),
    date: str | None = Query(None, description="Calendar date (YYYY-MM-DD), backward-compatible alias for a day filter"),
    timezone: str = Query("UTC", description="Timezone label for the requested calendar date"),
    analysis: bool = Query(True, description="Include conservative XAUUSD event intelligence"),
) -> EconomicEventListResponse:
    """Retrieve economic calendar releases with optional date and mode filters."""
    service = EconomicService(request.app.state.mongo_manager)
    return await service.list(
        limit=limit,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
        date=date,
        timezone=timezone,
        include_analysis=analysis,
    )
"""Economic-calendar route declarations."""

from fastapi import APIRouter, Query

from app.schemas.common import ErrorResponse
from app.schemas.economic import EconomicEventListResponse
from app.services.availability import require_feature


router = APIRouter(tags=["Economic Events"])
NOT_READY_RESPONSE = {501: {"model": ErrorResponse, "description": "Economic pipeline is not ready."}}


@router.get("/economic-events", response_model=EconomicEventListResponse, responses=NOT_READY_RESPONSE)
async def get_economic_events(limit: int = Query(default=50, ge=1, le=200)) -> EconomicEventListResponse:
    """Return normalized calendar events once Phase 7 is complete."""
    require_feature("Economic events", available_in_phase=7)
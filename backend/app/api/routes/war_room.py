"""Event War Room API routes."""
from fastapi import APIRouter, Query, Request

from app.schemas.common import ErrorResponse
from app.schemas.war_room import EventWarRoom, UpcomingWarRoomsResponse
from app.services.war_room import WarRoomService

router = APIRouter(prefix="/war-room", tags=["Event War Room"])


@router.get(
    "/upcoming",
    response_model=UpcomingWarRoomsResponse,
    responses={503: {"model": ErrorResponse}},
)
async def get_upcoming_war_rooms(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
) -> UpcomingWarRoomsResponse:
    """List upcoming macroeconomic events eligible for War Room analysis."""
    service = WarRoomService(request.app.state.mongo_manager)
    return await service.list_upcoming(limit=limit)


@router.get(
    "/{event_id}",
    response_model=EventWarRoom,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def get_event_war_room(
    request: Request,
    event_id: str,
    force_refresh: bool = Query(False),
) -> EventWarRoom:
    """Retrieve full War Room scenario and signal matrix analysis for a specific event."""
    service = WarRoomService(request.app.state.mongo_manager)
    return await service.get_war_room(event_id=event_id, force_refresh=force_refresh)

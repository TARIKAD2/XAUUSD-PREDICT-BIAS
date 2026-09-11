"""Financial-news route declarations."""

from fastapi import APIRouter, Query

from app.schemas.common import ErrorResponse
from app.schemas.news import NewsListResponse
from app.services.availability import require_feature


router = APIRouter(tags=["News"])
NOT_READY_RESPONSE = {501: {"model": ErrorResponse, "description": "News pipeline is not ready."}}


@router.get("/news", response_model=NewsListResponse, responses=NOT_READY_RESPONSE)
async def get_news(limit: int = Query(default=20, ge=1, le=100)) -> NewsListResponse:
    """Return normalized financial news once Phase 6 is complete."""
    require_feature("News data", available_in_phase=6)
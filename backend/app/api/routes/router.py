"""Top-level API router assembly."""

from fastapi import APIRouter

from .economic import router as economic_router
from .explanations import router as explanations_router
from .health import router as health_router
from .market import router as market_router
from .news import router as news_router
from .performance import router as performance_router
from .predictions import router as predictions_router
from .quality import router as quality_router
from .live_market import router as live_market_router
from .war_room import router as war_room_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(live_market_router)
api_router.include_router(market_router)
api_router.include_router(news_router)
api_router.include_router(economic_router)
api_router.include_router(predictions_router)
api_router.include_router(performance_router)
api_router.include_router(quality_router)
api_router.include_router(explanations_router)
api_router.include_router(war_room_router)


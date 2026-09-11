"""Market-data routes backed by verified normalized persistence."""
from fastapi import APIRouter, Query, Request
from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol, MarketDetailResponse, MarketOverviewResponse, Timeframe
from app.services.market import MarketService

router = APIRouter(tags=["Market Data"])
UNAVAILABLE = {503: {"model": ErrorResponse, "description": "Verified market data is unavailable."}}


@router.get("/market", response_model=MarketOverviewResponse, responses=UNAVAILABLE)
async def get_market_overview(request: Request, timeframe: Timeframe = Query(default=Timeframe.H1)) -> MarketOverviewResponse:
    return await MarketService(request.app.state.mongo_manager).overview(timeframe)


@router.get("/market/{symbol}", response_model=MarketDetailResponse, responses=UNAVAILABLE)
async def get_market_symbol(request: Request, symbol: AssetSymbol, timeframe: Timeframe = Query(default=Timeframe.H1), limit: int = Query(default=200, ge=1, le=5000)) -> MarketDetailResponse:
    return await MarketService(request.app.state.mongo_manager).detail(symbol, timeframe, limit)
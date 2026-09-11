"""Market-data route declarations."""

from fastapi import APIRouter, Query

from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol, MarketDetailResponse, MarketOverviewResponse, Timeframe
from app.services.availability import require_feature


router = APIRouter(tags=["Market Data"])
NOT_READY_RESPONSE = {501: {"model": ErrorResponse, "description": "Market pipeline is not ready."}}


@router.get("/market", response_model=MarketOverviewResponse, responses=NOT_READY_RESPONSE)
async def get_market_overview(timeframe: Timeframe = Query(default=Timeframe.H1)) -> MarketOverviewResponse:
    """Return the normalized snapshot collection once Phase 5 is complete."""
    require_feature("Market data", available_in_phase=5)


@router.get("/market/{symbol}", response_model=MarketDetailResponse, responses=NOT_READY_RESPONSE)
async def get_market_symbol(
    symbol: AssetSymbol, timeframe: Timeframe = Query(default=Timeframe.H1)
) -> MarketDetailResponse:
    """Return normalized OHLC data once Phase 5 is complete."""
    require_feature(f"Market data for {symbol.value}", available_in_phase=5)
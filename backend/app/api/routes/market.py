"""Market-data routes backed by verified normalized persistence."""
from fastapi import APIRouter, Query, Request, Response
from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol, MarketDetailResponse, MarketOverviewResponse, Timeframe
from app.services.market import MarketService

router = APIRouter(tags=["Market Data"])
UNAVAILABLE = {503: {"model": ErrorResponse, "description": "Verified market data is unavailable."}}


@router.get("/market", response_model=MarketOverviewResponse, responses=UNAVAILABLE)
async def get_market_overview(request: Request, response: Response, timeframe: Timeframe = Query(default=Timeframe.H1)) -> MarketOverviewResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return await MarketService(request.app.state.mongo_manager).overview(timeframe)


@router.get("/market/{symbol}", response_model=MarketDetailResponse, responses=UNAVAILABLE)
async def get_market_symbol(request: Request, response: Response, symbol: AssetSymbol, timeframe: Timeframe = Query(default=Timeframe.H1), limit: int = Query(default=200, ge=1, le=5000)) -> MarketDetailResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return await MarketService(request.app.state.mongo_manager).detail(symbol, timeframe, limit)


@router.post("/market/ingest-cycle")
@router.get("/market/cron-trigger")
async def trigger_ingest_cycle(request: Request, response: Response) -> dict:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    worker = getattr(request.app.state, "market_worker", None)
    if worker is None:
        from app.services.ingestion_worker import XAUUSDIngestionWorker
        worker = XAUUSDIngestionWorker(request.app.state.mongo_manager, request.app.state.settings)
    snapshot = await worker.run_once()
    return {"status": "ok", "worker_snapshot": snapshot}
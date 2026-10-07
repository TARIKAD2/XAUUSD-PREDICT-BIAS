"""Prediction routes – supports ?horizon=daily|weekly and /predictions/{symbol}/snapshot."""
from fastapi import APIRouter, Query, Request, Response
from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol
from app.schemas.prediction import PredictionListResponse, PredictionResponse, PredictionSnapshotResponse
from app.services.predictions import PredictionService

router = APIRouter(tags=["Predictions"])


@router.get(
    "/predictions",
    response_model=PredictionListResponse,
    responses={503: {"model": ErrorResponse}},
)
async def predictions(request: Request, response: Response) -> PredictionListResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return await PredictionService(request.app.state.mongo_manager).all()


@router.get(
    "/predictions/{symbol}/snapshot",
    response_model=PredictionSnapshotResponse,
    responses={503: {"model": ErrorResponse}},
)
async def prediction_snapshot(
    symbol: AssetSymbol,
    request: Request,
    response: Response,
    force_recalculate: bool = Query(default=False, description="Force server-side recalculation"),
) -> PredictionSnapshotResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return await PredictionService(request.app.state.mongo_manager).get_latest_snapshot(
        symbol, force_recalculate=force_recalculate
    )


@router.get(
    "/predictions/{symbol}",
    response_model=PredictionResponse,
    responses={503: {"model": ErrorResponse}},
)
async def prediction(
    symbol: AssetSymbol,
    request: Request,
    response: Response,
    horizon: str = Query(default="daily", description="Forecast horizon: 'daily' (24H) or 'weekly' (120H)"),
) -> PredictionResponse:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return await PredictionService(request.app.state.mongo_manager).one(symbol, horizon=horizon)
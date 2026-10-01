from fastapi import APIRouter, Query, Request

from app.schemas.common import ErrorResponse
from app.schemas.market import Timeframe
from app.schemas.quality import DataQualityResponse
from app.services.quality import DataQualityService

router = APIRouter(tags=["Data Quality"])


@router.get("/data-quality", response_model=DataQualityResponse, responses={503: {"model": ErrorResponse}})
async def get_data_quality(
    request: Request,
    timeframe: Timeframe = Query(default=Timeframe.H1),
) -> DataQualityResponse:
    worker = getattr(request.app.state, "market_worker", None)
    worker_status = worker.snapshot() if worker is not None else None
    return await DataQualityService(request.app.state.mongo_manager, worker_status).report(timeframe)

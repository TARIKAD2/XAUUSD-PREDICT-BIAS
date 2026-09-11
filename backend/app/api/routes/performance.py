"""Model-performance route declarations."""

from fastapi import APIRouter

from app.schemas.common import ErrorResponse
from app.schemas.performance import ModelPerformanceResponse
from app.services.availability import require_feature


router = APIRouter(tags=["Model Performance"])
NOT_READY_RESPONSE = {501: {"model": ErrorResponse, "description": "Model metrics are not ready."}}


@router.get("/model-performance", response_model=ModelPerformanceResponse, responses=NOT_READY_RESPONSE)
async def get_model_performance() -> ModelPerformanceResponse:
    """Return out-of-sample model metrics after Phase 9 is complete."""
    require_feature("Model performance", available_in_phase=9)
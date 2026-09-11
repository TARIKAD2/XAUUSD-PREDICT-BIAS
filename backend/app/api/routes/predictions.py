"""Prediction route declarations."""

from fastapi import APIRouter

from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol
from app.schemas.prediction import PredictionListResponse, PredictionResponse
from app.services.availability import require_feature


router = APIRouter(tags=["Predictions"])
NOT_READY_RESPONSE = {501: {"model": ErrorResponse, "description": "Prediction pipeline is not ready."}}


@router.get("/predictions", response_model=PredictionListResponse, responses=NOT_READY_RESPONSE)
async def get_predictions() -> PredictionListResponse:
    """Return model estimates after Phase 11 has completed."""
    require_feature("Predictions", available_in_phase=11)


@router.get("/predictions/{symbol}", response_model=PredictionResponse, responses=NOT_READY_RESPONSE)
async def get_prediction(symbol: AssetSymbol) -> PredictionResponse:
    """Return one evidence-based estimate after Phase 11 has completed."""
    require_feature(f"Predictions for {symbol.value}", available_in_phase=11)
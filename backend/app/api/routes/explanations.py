from fastapi import APIRouter, Request

from app.schemas.common import ErrorResponse
from app.schemas.explanation import ExplanationResponse
from app.schemas.market import AssetSymbol
from app.services.explanations import ExplanationService

router = APIRouter(tags=["Explanations"])


@router.get("/explanations/{symbol}", response_model=ExplanationResponse, responses={503: {"model": ErrorResponse}})
async def get_explanation(symbol: AssetSymbol, request: Request) -> ExplanationResponse:
    return await ExplanationService(request.app.state.mongo_manager).for_symbol(symbol)

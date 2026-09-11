from fastapi import APIRouter,Request
from app.schemas.common import ErrorResponse
from app.schemas.market import AssetSymbol
from app.schemas.prediction import PredictionListResponse,PredictionResponse
from app.services.predictions import PredictionService
router=APIRouter(tags=["Predictions"])
@router.get("/predictions",response_model=PredictionListResponse,responses={503:{"model":ErrorResponse}})
async def predictions(request:Request)->PredictionListResponse:return await PredictionService(request.app.state.mongo_manager).all()
@router.get("/predictions/{symbol}",response_model=PredictionResponse,responses={503:{"model":ErrorResponse}})
async def prediction(symbol:AssetSymbol,request:Request)->PredictionResponse:return await PredictionService(request.app.state.mongo_manager).one(symbol)
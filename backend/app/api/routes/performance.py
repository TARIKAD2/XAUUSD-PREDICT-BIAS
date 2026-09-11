from fastapi import APIRouter,Request
from app.schemas.common import ErrorResponse
from app.schemas.performance import ModelPerformanceResponse
from app.services.performance import ModelPerformanceService
router=APIRouter(tags=["Model Performance"])
@router.get("/model-performance",response_model=ModelPerformanceResponse,responses={503:{"model":ErrorResponse}})
async def get_model_performance(request:Request)->ModelPerformanceResponse:return await ModelPerformanceService(request.app.state.mongo_manager).list()
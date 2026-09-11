"""Economic-calendar routes."""
from fastapi import APIRouter,Query,Request
from app.schemas.common import ErrorResponse
from app.schemas.economic import EconomicEventListResponse
from app.services.economic import EconomicService
router=APIRouter(tags=["Economic Events"])
@router.get("/economic-events",response_model=EconomicEventListResponse,responses={503:{"model":ErrorResponse}})
async def get_economic_events(request:Request,limit:int=Query(50,ge=1,le=200))->EconomicEventListResponse:return await EconomicService(request.app.state.mongo_manager).list(limit)
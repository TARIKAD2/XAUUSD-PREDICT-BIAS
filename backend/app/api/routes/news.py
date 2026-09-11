from fastapi import APIRouter,Query,Request
from app.schemas.common import ErrorResponse
from app.schemas.news import NewsListResponse
from app.services.news import NewsService
router=APIRouter(tags=["News"])
@router.get("/news",response_model=NewsListResponse,responses={503:{"model":ErrorResponse}})
async def get_news(request:Request,limit:int=Query(20,ge=1,le=100))->NewsListResponse: return await NewsService(request.app.state.mongo_manager).list(limit)
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.common import ErrorDetail,ErrorResponse
from app.services.availability import FeatureNotReadyError
from app.services.market import MarketDataUnavailableError
from app.services.news import NewsUnavailableError
def _response(status_code:int,code:str,message:str)->JSONResponse:return JSONResponse(status_code=status_code,content=ErrorResponse(error=ErrorDetail(code=code,message=message)).model_dump(mode="json"))
async def feature_not_ready_handler(request:Request,exception:FeatureNotReadyError)->JSONResponse:return _response(501,"feature_not_ready",str(exception))
async def market_data_unavailable_handler(request:Request,exception:MarketDataUnavailableError)->JSONResponse:return _response(503,"market_data_unavailable",str(exception))
async def news_unavailable_handler(request:Request,exception:NewsUnavailableError)->JSONResponse:return _response(503,"news_unavailable",str(exception))
"""Consistent non-sensitive API error responses."""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas.common import ErrorDetail,ErrorResponse
from app.services.availability import FeatureNotReadyError
from app.services.market import MarketDataUnavailableError
from app.services.news import NewsUnavailableError
from app.services.economic import EconomicDataUnavailableError
def response(status,code,message):return JSONResponse(status_code=status,content=ErrorResponse(error=ErrorDetail(code=code,message=message)).model_dump(mode="json"))
async def feature_not_ready_handler(request:Request,e:FeatureNotReadyError):return response(501,"feature_not_ready",str(e))
async def market_data_unavailable_handler(request:Request,e:MarketDataUnavailableError):return response(503,"market_data_unavailable",str(e))
async def news_unavailable_handler(request:Request,e:NewsUnavailableError):return response(503,"news_unavailable",str(e))
async def economic_unavailable_handler(request:Request,e:EconomicDataUnavailableError):return response(503,"economic_data_unavailable",str(e))
from app.services.predictions import PredictionUnavailableError
async def prediction_unavailable_handler(request:Request,e:PredictionUnavailableError):return response(503,'prediction_unavailable',str(e))

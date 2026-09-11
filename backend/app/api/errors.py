"""Exception handlers that keep public errors consistent and non-sensitive."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse
from app.services.availability import FeatureNotReadyError


async def feature_not_ready_handler(
    request: Request, exception: FeatureNotReadyError
) -> JSONResponse:
    """Return an honest response while an upstream pipeline is still absent."""
    payload = ErrorResponse(
        error=ErrorDetail(code="feature_not_ready", message=str(exception))
    )
    return JSONResponse(status_code=501, content=payload.model_dump(mode="json"))
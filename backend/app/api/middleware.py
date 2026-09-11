"""HTTP middleware for request correlation and structured access logging."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from app.core.logging import get_logger


logger = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next) -> Response:
    """Attach a server-generated request ID and log safe request metadata."""
    request_id = str(uuid4())
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "http_request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )
        raise

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        },
    )
    return response
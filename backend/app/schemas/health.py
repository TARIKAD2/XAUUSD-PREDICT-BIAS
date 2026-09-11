"""Health endpoint schemas."""

from datetime import datetime
from typing import Literal

from .base import APIModel


class HealthResponse(APIModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    timestamp: datetime
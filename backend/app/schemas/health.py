"""Health endpoint schemas."""

from datetime import datetime
from typing import Literal

from app.models.database import DatabaseConnectionStatus

from .base import APIModel


class DatabaseHealth(APIModel):
    status: DatabaseConnectionStatus


class HealthResponse(APIModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    timestamp: datetime
    database: DatabaseHealth
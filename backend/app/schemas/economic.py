"""Schemas for normalized economic-calendar events."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base import APIModel


class EventImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EconomicEvent(APIModel):
    event: str
    country: str = Field(min_length=2, max_length=3)
    currency: str = Field(min_length=3, max_length=3)
    timestamp: datetime
    actual: float | None = None
    forecast: float | None = None
    previous: float | None = None
    revision: float | None = None
    surprise: float | None = None
    importance: EventImportance


class EconomicEventListResponse(APIModel):
    items: list[EconomicEvent]
    generated_at: datetime
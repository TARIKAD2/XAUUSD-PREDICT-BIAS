"""Schemas for normalized economic-calendar events."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base import APIModel


class EventImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventStatus(str, Enum):
    PUBLISHED = "published"
    UNAVAILABLE = "unavailable"
    SCHEDULED = "scheduled"
    REVISED = "revised"


class CalendarEventStatus(str, Enum):
    RELEASED = "RELEASED"
    UPCOMING = "UPCOMING"
    UNKNOWN = "UNKNOWN"


class ProviderStatus(str, Enum):
    OK = "OK"
    NO_DATA = "NO_DATA"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PARTIAL_DATA = "PARTIAL_DATA"


class EconomicEvent(APIModel):
    event: str
    event_name: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=3)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    timestamp: datetime
    scheduled_at: datetime | None = None
    actual: float | None = None
    forecast: float | None = None
    consensus: float | None = None
    previous: float | None = None
    revision: float | None = None
    surprise: float | None = None
    importance: EventImportance
    source: str = "unknown"
    status: EventStatus = EventStatus.UNAVAILABLE
    event_id: str | None = None
    provider: str | None = None
    provider_event_id: str | None = None
    indicator: str | None = None
    release_time_utc: datetime | None = None
    observation_period: str | None = None
    revised_previous: float | None = None
    unit: str | None = None
    retrieved_at_utc: datetime | None = None
    vintage_time_utc: datetime | None = None
    source_timestamp: datetime | None = None
    calendar_status: CalendarEventStatus = CalendarEventStatus.UNKNOWN
    related_group: str | None = None
    related_events: list[str] = Field(default_factory=list)
    macro_theme: str | None = None
    information_available_at: datetime | None = None
    source_url: str | None = None
    all_day: bool | None = None
    raw: dict | None = None


class EconomicEventListResponse(APIModel):
    items: list[EconomicEvent]
    generated_at: datetime
    status: ProviderStatus = ProviderStatus.OK
    provider_statuses: dict[str, ProviderStatus] = Field(default_factory=dict)
    date: str | None = None
    timezone: str = "UTC"
    analysis: dict | None = None
    attribution_url: str | None = None

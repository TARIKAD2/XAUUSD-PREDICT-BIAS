"""Pydantic schemas for the Event War Room."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from .base import APIModel


class SignalStatus(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class ExpectedOutcomeProbabilities(APIModel):
    cool_pct: float
    inline_pct: float
    hot_pct: float
    rationale: str


class ExpectedMetricItem(APIModel):
    name: str
    forecast: float | None = None
    previous: float | None = None
    actual: float | None = None
    unit: str | None = None


class SignalMatrixFactor(APIModel):
    factor: str
    status: SignalStatus
    reason: str
    indicator_value: str | None = None


class WarRoomScenario(APIModel):
    name: str  # "COOL / SOFT", "IN-LINE", "HOT"
    probability: float
    expected_direction: SignalStatus
    target_range: str
    assumptions: str
    invalidation: str
    risk_note: str


class WarRoomVerdict(APIModel):
    dominant_scenario: str
    bias: SignalStatus
    main_drivers: list[str]
    main_risk: str
    invalidation_condition: str
    disclaimer: str = (
        "Scenario analysis based on quantitative technical modeling, historical macroeconomic "
        "correlations, and ML telemetry. Not guaranteed prediction or financial advice."
    )


class EventWarRoom(APIModel):
    event_id: str
    event_name: str
    timestamp: datetime
    importance: str
    country: str = "US"
    currency: str = "USD"
    current_xau_price: float
    market_context: str
    probabilities: ExpectedOutcomeProbabilities
    expected_metrics: list[ExpectedMetricItem]
    signal_matrix: list[SignalMatrixFactor]
    scenarios: list[WarRoomScenario]
    verdict: WarRoomVerdict
    generated_at: datetime
    cached: bool = False


class UpcomingWarRoomItem(APIModel):
    event_id: str
    event_name: str
    timestamp: datetime
    importance: str
    country: str
    currency: str
    actual: float | None = None
    forecast: float | None = None
    previous: float | None = None
    status: str
    preview_bias: SignalStatus | None = None


class UpcomingWarRoomsResponse(APIModel):
    items: list[UpcomingWarRoomItem]
    generated_at: datetime

"""Conservative event intelligence for XAUUSD (never uses future information)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.schemas.economic import EconomicEvent


@dataclass(frozen=True)
class EventIntelligenceResult:
    status: str
    comparable_events: int
    bias: str | None = None
    bullish_probability: float | None = None
    neutral_probability: float | None = None
    bearish_probability: float | None = None
    confidence: float | None = None
    reasons: list[str] | None = None
    related_events: list[str] | None = None
    risk_factors: list[str] | None = None
    invalidation: list[str] | None = None


class XAUUSDEventIntelligence:
    """Summarize released comparable events using only information available by as_of."""

    def analyze(
        self,
        events: list[EconomicEvent],
        *,
        as_of: datetime | None = None,
        minimum_comparables: int = 3,
    ) -> EventIntelligenceResult:
        cutoff = as_of or datetime.now(UTC)
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=UTC)
        eligible = [
            event for event in events
            if event.actual is not None
            and event.forecast is not None
            and (event.information_available_at or event.scheduled_at or event.timestamp) <= cutoff
        ]
        if len(eligible) < minimum_comparables:
            return EventIntelligenceResult(
                status="INSUFFICIENT_EVENT_DATA",
                comparable_events=len(eligible),
                reasons=[f"Need {minimum_comparables} released comparable events; found {len(eligible)}."],
                related_events=[],
                risk_factors=["Forecast or release-time data is unavailable for enough events."],
                invalidation=["Analysis remains unavailable until comparable released events exist."],
            )
        scores: list[float] = []
        reasons: list[str] = []
        for event in eligible:
            denominator = abs(event.forecast or 0.0) or 1.0
            surprise = (event.actual or 0.0) - (event.forecast or 0.0)
            normalized = surprise / denominator
            name = (event.event_name or event.event).casefold()
            # For inflation, hotter-than-expected data is generally adverse to gold;
            # for growth/labor, stronger data is treated as USD/yield-positive.
            gold_sign = -1.0 if any(term in name for term in ("cpi", "ppi", "inflation", "payroll", "employment", "gdp", "retail")) else 1.0
            scores.append(max(-1.0, min(1.0, normalized * gold_sign)))
            reasons.append(f"{event.event_name or event.event}: actual versus forecast is {surprise:+g}.")
        mean_score = sum(scores) / len(scores)
        magnitude = min(1.0, abs(mean_score))
        bullish = (1.0 + mean_score) / 2.0
        bearish = (1.0 - mean_score) / 2.0
        neutral = max(0.0, 1.0 - magnitude)
        total = bullish + neutral + bearish
        bullish, neutral, bearish = bullish / total, neutral / total, bearish / total
        bias = "BULLISH" if bullish > bearish and bullish > neutral else "BEARISH" if bearish > bullish and bearish > neutral else "NEUTRAL"
        confidence = max(bullish, neutral, bearish)
        related = sorted({name for event in eligible for name in event.related_events})
        return EventIntelligenceResult(
            status="OK",
            comparable_events=len(eligible),
            bias=bias,
            bullish_probability=bullish,
            neutral_probability=neutral,
            bearish_probability=bearish,
            confidence=confidence,
            reasons=reasons,
            related_events=related,
            risk_factors=["Interpretation is research-only and excludes unavailable USD/yield context."],
            invalidation=["A later revision or contradictory macro release can invalidate this signal."],
        )


def analyze_xauusd_events(events: list[EconomicEvent], as_of: datetime | None = None) -> EventIntelligenceResult:
    return XAUUSDEventIntelligence().analyze(events, as_of=as_of)

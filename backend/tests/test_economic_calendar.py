from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.collectors.economic import deduplicate_events, group_related_events, normalize_event
from app.core.config import Settings
from app.providers.trading_economics import TradingEconomicsProvider
from app.providers.financecalendar import FinanceCalendarProvider
from app.schemas.economic import ProviderStatus
from app.services.xauusd_event_intelligence import XAUUSDEventIntelligence


def _raw(**overrides):
    return {
        "event": "CPI",
        "country": "US",
        "currency": "USD",
        "timestamp": "2026-01-01T13:30:00Z",
        "actual": 3.2,
        "forecast": 3.0,
        "previous": 2.9,
        "importance": "high",
        "provider": "trading_economics",
        "provider_event_id": "cpi-1",
        **overrides,
    }


def test_normalization_deduplication_and_relationships_are_deterministic():
    first = normalize_event(_raw())
    richer = normalize_event(_raw(actual_at="2026-01-01T13:31:00Z", unit="%"))
    assert first.information_available_at is None
    assert richer.information_available_at.isoformat().startswith("2026-01-01T13:31")
    grouped = group_related_events(deduplicate_events([first, richer]))
    assert len(grouped) == 1
    assert grouped[0].related_group


@pytest.mark.asyncio
async def test_provider_statuses():
    not_configured = await TradingEconomicsProvider(Settings(trading_economics_api_key=None)).fetch()
    assert not_configured.status == ProviderStatus.NOT_CONFIGURED

    async def handler(request):
        return httpx.Response(200, json=[{"Event": "CPI", "Country": "US", "Currency": "USD", "Date": "2026-01-01T13:30:00Z"}])

    settings = Settings(trading_economics_api_key="test-key")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await TradingEconomicsProvider(settings, client=client).fetch()
    assert result.status == ProviderStatus.PARTIAL_DATA
    assert result.events[0].provider == "trading_economics"


@pytest.mark.asyncio
async def test_financecalendar_normalizes_nullable_fields_and_numeric_surprise():
    async def handler(request):
        assert request.url.path == "/today"
        return httpx.Response(200, json=[{
            "id": "release-1",
            "event": "Policy decision",
            "date": "2026-01-01T13:30:00Z",
            "time_utc": "2026-01-01T13:30:00Z",
            "actual": "not released",
            "forecast": "2.5",
            "country": None,
            "currency": None,
        }])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await FinanceCalendarProvider(client=client, base_url="https://calendar.test").fetch()

    assert result.status == ProviderStatus.PARTIAL_DATA
    event = result.events[0]
    assert event.country is None
    assert event.currency is None
    assert event.scheduled_at is not None
    assert event.surprise is None
    assert event.event_id == "release-1"


@pytest.mark.asyncio
async def test_financecalendar_filters_today_to_requested_date_and_preserves_all_day():
    async def handler(request):
        assert request.url.path == "/today"
        return httpx.Response(200, json={
            "date": "2026-01-02",
            "events": [
                {
                    "event": "Current holiday",
                    "date": "2026-01-02",
                    "time_utc": None,
                    "all_day": True,
                    "impact": "low",
                },
                {
                    "event": "Stale holiday",
                    "date": "2026-01-01",
                    "time_utc": None,
                    "all_day": True,
                    "impact": "low",
                },
            ],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await FinanceCalendarProvider(client=client, base_url="https://calendar.test").fetch(
            mode="today",
            start="2026-01-02",
            end="2026-01-02",
        )

    assert result.status == ProviderStatus.PARTIAL_DATA
    assert len(result.events) == 1
    assert result.events[0].event == "Current holiday"
    assert result.events[0].scheduled_at is None
    assert result.events[0].all_day is True


@pytest.mark.asyncio
async def test_financecalendar_returns_no_data_when_provider_date_mismatches():
    async def handler(request):
        return httpx.Response(200, json={
            "date": "2026-01-01",
            "events": [{"event": "Stale event", "date": "2026-01-01", "impact": "high"}],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await FinanceCalendarProvider(client=client, base_url="https://calendar.test").fetch(
            mode="today",
            start="2026-01-02",
            end="2026-01-02",
        )

    assert result.status == ProviderStatus.NO_DATA
    assert result.events == []


@pytest.mark.asyncio
async def test_financecalendar_calendar_uses_inclusive_strict_date_range():
    async def handler(request):
        assert request.url.path == "/calendar"
        assert request.url.params["from"] == "2026-01-02"
        assert request.url.params["to"] == "2026-01-03"
        return httpx.Response(200, json={
            "events": [
                {"event": "Start", "date": "2026-01-02", "impact": "medium"},
                {"event": "End", "date": "2026-01-03", "impact": "medium"},
                {"event": "Outside", "date": "2026-01-04", "impact": "medium"},
            ],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await FinanceCalendarProvider(client=client, base_url="https://calendar.test").fetch(
            mode="calendar",
            start="2026-01-02",
            end="2026-01-03",
        )

    assert {event.event for event in result.events} == {"Start", "End"}


def test_analysis_does_not_look_ahead():
    now = datetime(2026, 1, 2, tzinfo=UTC)
    events = [
        normalize_event(_raw(provider_event_id=str(index), timestamp=(now - timedelta(days=index)).isoformat()))
        for index in range(3)
    ]
    future = normalize_event(_raw(provider_event_id="future", timestamp=(now + timedelta(days=1)).isoformat()))
    result = XAUUSDEventIntelligence().analyze(events + [future], as_of=now)
    assert result.status == "OK"
    assert result.comparable_events == 3

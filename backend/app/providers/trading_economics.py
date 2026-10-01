"""Trading Economics calendar adapter with explicit availability semantics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from app.collectors.economic import normalize_event, deduplicate_events, group_related_events
from app.core.config import Settings
from app.schemas.economic import EconomicEvent, ProviderStatus


@dataclass
class ProviderResult:
    events: list[EconomicEvent] = field(default_factory=list)
    status: ProviderStatus = ProviderStatus.NO_DATA
    provider: str = "trading_economics"
    error: str | None = None

    @property
    def provider_status(self) -> ProviderStatus:
        """Compatibility name used by API orchestration callers."""
        return self.status


class TradingEconomicsProvider:
    """Fetch the calendar without ever embedding credentials in source."""

    name = "trading_economics"
    endpoint = "https://api.tradingeconomics.com/calendar/country/United States"

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client

    async def fetch(self, start: str | None = None, end: str | None = None) -> ProviderResult:
        key = self.settings.trading_economics_api_key
        if key is None or not key.get_secret_value().strip():
            return ProviderResult(status=ProviderStatus.NOT_CONFIGURED)
        params: dict[str, Any] = {"c": key.get_secret_value()}
        if start:
            params["d1"] = start
        if end:
            params["d2"] = end
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=self.settings.request_timeout_seconds)
        try:
            response = await client.get(self.endpoint, params=params)
            if response.status_code >= 500:
                return ProviderResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, error=f"http_{response.status_code}")
            if response.status_code >= 400:
                return ProviderResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, error=f"http_{response.status_code}")
            payload = response.json()
            if not isinstance(payload, list):
                return ProviderResult(status=ProviderStatus.NO_DATA)
            events: list[EconomicEvent] = []
            invalid = 0
            incomplete = 0
            for item in payload:
                try:
                    if not item.get("Event") and not item.get("event"):
                        invalid += 1
                        continue
                    if not item.get("Date") and not item.get("date"):
                        invalid += 1
                        continue
                    expected_fields = ("Actual", "Forecast", "Previous", "Importance")
                    if any(item.get(key) in (None, "") and item.get(key.lower()) in (None, "") for key in expected_fields):
                        incomplete += 1
                    events.append(normalize_event({
                        **item,
                        "event": item.get("event") or item.get("Event"),
                        "event_name": item.get("event") or item.get("Event"),
                        "country": item.get("country") or item.get("Country") or "US",
                        "currency": item.get("currency") or item.get("Currency") or "USD",
                        "timestamp": item.get("date") or item.get("Date"),
                        "scheduled_at": item.get("date") or item.get("Date"),
                        "actual": item.get("actual") if "actual" in item else item.get("Actual"),
                        "forecast": item.get("forecast") if "forecast" in item else item.get("Forecast"),
                        "previous": item.get("previous") if "previous" in item else item.get("Previous"),
                        "revised_previous": item.get("revised_previous")
                        if "revised_previous" in item
                        else item.get("Revised"),
                        "event_id": item.get("id") or item.get("ID"),
                        "provider": self.name,
                        "source": self.name,
                        "provider_event_id": item.get("id") or item.get("ID"),
                        "source_timestamp": item.get("lastupdate") or item.get("LastUpdate") or item.get("date") or item.get("Date"),
                        "information_available_at": item.get("actualdate") or item.get("ActualDate"),
                        "importance": str(item.get("importance") or item.get("Importance") or "medium").lower(),
                    }))
                except (TypeError, ValueError, KeyError):
                    invalid += 1
            events = group_related_events(deduplicate_events(events))
            status = (
                ProviderStatus.PARTIAL_DATA
                if (invalid or incomplete)
                else ProviderStatus.NO_DATA
                if not events
                else ProviderStatus.OK
            )
            return ProviderResult(events=events, status=status)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            return ProviderResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, error=type(exc).__name__)
        finally:
            if owns_client:
                await client.aclose()

    async def fetch_events(self, start: str | None = None, end: str | None = None) -> ProviderResult:
        """Explicit alias for callers that distinguish fetching from normalization."""
        return await self.fetch(start=start, end=end)


EconomicProviderResult = ProviderResult

"""Adapter for the keyless FinanceCalendar economic-calendar API."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import httpx

from app.collectors.economic import deduplicate_events, group_related_events, normalize_event
from app.schemas.economic import EconomicEvent, ProviderStatus


@dataclass
class FinanceCalendarResult:
    events: list[EconomicEvent] = field(default_factory=list)
    status: ProviderStatus = ProviderStatus.NO_DATA
    provider: str = "financecalendar"
    error: str | None = None

    @property
    def provider_status(self) -> ProviderStatus:
        return self.status


class FinanceCalendarProvider:
    """Fetch FinanceCalendar's official ``/today`` and ``/calendar`` resources.

    The API is public and deliberately receives no credentials.  A short,
    in-process cache prevents repeated route requests while bounded retries
    avoid turning a provider outage into request amplification.
    """

    name = "financecalendar"
    base_url = "https://www.financecalendar.com/wp-json/fc/v1"
    BASE_URL = base_url
    max_retries = 2
    cache_ttl_seconds = 30
    def __init__(self, client: httpx.AsyncClient | None = None, *, base_url: str | None = None, enabled: bool = True) -> None:
        self.client = client
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.enabled = enabled
        self._cache: dict[tuple[str, str | None, str | None], tuple[float, FinanceCalendarResult]] = {}

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            text = str(value).strip().replace(",", "")
            return float(text) if text and text.lower() not in {"n/a", "na", "null", "none", "-"} else None
        except (TypeError, ValueError):
            return None

    def _event(self, item: dict[str, Any]) -> EconomicEvent:
        name = item.get("event_name") or item.get("event") or item.get("title") or item.get("name")
        if not name:
            raise ValueError("missing event name")
        scheduled = item.get("scheduled_at") or item.get("time_utc") or item.get("datetime") or item.get("time")
        timestamp = scheduled or item.get("timestamp") or item.get("release_time_utc") or item.get("date")
        if not timestamp:
            raise ValueError("missing event timestamp")
        actual = self._number(item.get("actual"))
        forecast = self._number(item.get("forecast") if item.get("forecast") is not None else item.get("consensus"))
        previous = self._number(item.get("previous") if item.get("previous") is not None else item.get("prior"))
        provider_id = item.get("id") or item.get("event_id")
        if not provider_id:
            provider_id = "|".join(
                str(value or "").strip().casefold()
                for value in (
                    item.get("url"),
                    name,
                    item.get("date"),
                    scheduled,
                    item.get("category"),
                )
            )
        raw = {
            "event": str(name),
            "event_name": str(name),
            "country": item.get("country"),
            "currency": item.get("currency"),
            "timestamp": timestamp,
            "scheduled_at": scheduled,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "importance": str(item.get("importance") or item.get("impact") or "medium").lower(),
            "status": item.get("status"),
            "provider": self.name,
            "source": self.name,
            "event_id": str(provider_id),
            "provider_event_id": str(provider_id),
            "source_url": item.get("source_url") or item.get("url"),
            "all_day": item.get("all_day"),
            "raw": item,
        }
        return normalize_event(raw, preserve_nullable_scheduled_at=True)

    @staticmethod
    def _event_date(item: dict[str, Any]) -> date | None:
        value = item.get("date")
        if value:
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                pass
        for field in ("scheduled_at", "time_utc", "datetime", "timestamp", "release_time_utc"):
            value = item.get(field)
            if not value:
                continue
            try:
                return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
            except ValueError:
                continue
        return None

    @classmethod
    def _is_in_requested_range(
        cls,
        item: dict[str, Any],
        *,
        start: str | None,
        end: str | None,
    ) -> bool:
        if not start and not end:
            return True
        event_date = cls._event_date(item)
        if event_date is None:
            return False
        start_date = date.fromisoformat(start) if start else None
        end_date = date.fromisoformat(end) if end else None
        return (start_date is None or event_date >= start_date) and (end_date is None or event_date <= end_date)

    async def fetch(self, *, mode: str = "today", start: str | None = None, end: str | None = None) -> FinanceCalendarResult:
        if mode not in {"today", "calendar"}:
            raise ValueError("mode must be today or calendar")
        if not self.enabled:
            return FinanceCalendarResult(status=ProviderStatus.NOT_CONFIGURED)
        key = (mode, start, end)
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl_seconds:
            return cached[1]
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15)
        params = {key: value for key, value in {"from": start, "to": end}.items() if value}
        if mode == "today":
            params = {}
        try:
            response = None
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(f"{self.base_url}/{mode}", params=params)
                    if response.status_code < 500:
                        break
                except httpx.HTTPError:
                    if attempt == self.max_retries:
                        raise
                await asyncio.sleep(0.05 * (2**attempt))
            if response is None or response.status_code >= 400:
                result = FinanceCalendarResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, error=f"http_{response.status_code if response else 'error'}")
            else:
                payload = response.json()
                rows = payload if isinstance(payload, list) else payload.get("events", payload.get("data", [])) if isinstance(payload, dict) else []
                invalid = 0
                events = []
                incomplete = 0
                filtered_rows = [
                    row for row in rows
                    if isinstance(row, dict) and self._is_in_requested_range(
                        row,
                        start=start,
                        end=end,
                    )
                ] if isinstance(rows, list) else []
                for row in filtered_rows:
                    try:
                        if any(row.get(field) in (None, "") for field in ("consensus", "prior", "actual", "impact", "category")):
                            incomplete += 1
                        events.append(self._event(row))
                    except (TypeError, ValueError, KeyError):
                        invalid += 1
                events = group_related_events(deduplicate_events(events))
                result = FinanceCalendarResult(
                    events=events,
                    status=ProviderStatus.PARTIAL_DATA
                    if invalid or incomplete
                    else (ProviderStatus.OK if events else ProviderStatus.NO_DATA),
                )
        except (httpx.HTTPError, ValueError, TypeError):
            result = FinanceCalendarResult(status=ProviderStatus.PROVIDER_UNAVAILABLE, error="request_failed")
        finally:
            if owns_client:
                await client.aclose()
        self._cache[key] = (time.monotonic(), result)
        return result

    async def fetch_events(self, **kwargs: Any) -> FinanceCalendarResult:
        return await self.fetch(**kwargs)

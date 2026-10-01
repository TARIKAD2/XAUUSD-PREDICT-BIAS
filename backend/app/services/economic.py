"""Economic-calendar persistence and retrieval."""
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.collectors.economic import normalize_event, deduplicate_events, group_related_events
from app.db.client import MongoClientManager
from app.db.collections import ECONOMIC_EVENTS
from app.db.repositories import MongoRepository
from app.schemas.economic import (
    CalendarEventStatus,
    EconomicEvent,
    EconomicEventListResponse,
    ProviderStatus,
)
from app.providers.trading_economics import TradingEconomicsProvider
from app.providers.financecalendar import FinanceCalendarProvider


class EconomicDataUnavailableError(RuntimeError):
    pass


class EconomicService:
    def __init__(self, manager: MongoClientManager):
        self.manager = manager
        self.repo = MongoRepository(manager, ECONOMIC_EVENTS)

    async def upsert_raw(self, raw: dict) -> EconomicEvent:
        event = normalize_event(raw)
        doc = event.model_dump(mode="python") | {"ingested_at": datetime.now(UTC)}
        await self.repo.upsert_one(
            {"event": event.event, "country": event.country, "currency": event.currency, "timestamp": event.timestamp},
            doc,
        )
        return event

    async def save_events(self, events: list[EconomicEvent]) -> int:
        for event in events:
            doc = event.model_dump(mode="python")
            doc["ingested_at"] = datetime.now(UTC)
            await self.repo.upsert_one(
                {"event": event.event, "country": event.country, "currency": event.currency, "timestamp": event.timestamp},
                doc,
            )
        return len(events)

    async def ingest_from_collectors(self, collectors: list) -> int:
        saved = 0
        for collector in collectors:
            try:
                events = await collector.fetch()
            except Exception:
                continue
            saved += await self.save_events(events)
        return saved

    async def list(
        self,
        limit: int = 50,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        mode: str | None = None,
        date: str | None = None,
        timezone: str = "UTC",
        include_analysis: bool = False,
    ) -> EconomicEventListResponse:
        """List events without falling back to stale records."""
        if not self.manager.is_connected:
            raise EconomicDataUnavailableError("Economic-event storage is unavailable.")

        query: dict = {}
        now = datetime.now(UTC)
        try:
            calendar_zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            calendar_zone = ZoneInfo("UTC")
            timezone = "UTC"
        calendar_now = now.astimezone(calendar_zone)
        local_start = calendar_now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = local_start.astimezone(UTC)
        day_end = (local_start + timedelta(days=1)).astimezone(UTC)
        if date and not (start_date or end_date):
            start_date = f"{date}T00:00:00+00:00"
            end_date = f"{date}T23:59:59.999999+00:00"
        effective_mode = mode or ("all" if start_date or end_date else "today")

        if effective_mode == "today":
            query["timestamp"] = {"$gte": day_start, "$lt": day_end}
        elif effective_mode == "upcoming":
            query["timestamp"] = {"$gte": now}
        elif effective_mode not in {"all", "released", "unknown"}:
            raise ValueError(f"Unsupported economic-events mode: {effective_mode}")
        elif start_date or end_date:
            ts_filter = {}
            if start_date:
                s_dt = datetime.fromisoformat(str(start_date).replace("Z", "+00:00")) if isinstance(start_date, str) else start_date
                ts_filter["$gte"] = s_dt.replace(tzinfo=UTC) if s_dt.tzinfo is None else s_dt.astimezone(UTC)
            if end_date:
                e_dt = datetime.fromisoformat(str(end_date).replace("Z", "+00:00")) if isinstance(end_date, str) else end_date
                ts_filter["$lte"] = e_dt.replace(tzinfo=UTC) if e_dt.tzinfo is None else e_dt.astimezone(UTC)
            if ts_filter:
                query["timestamp"] = ts_filter

        docs = await self.repo.find_recent(query, limit)

        items = []
        for d in docs:
            try:
                cleaned = {k: v for k, v in d.items() if k != "_id"}
                cleaned.setdefault("event_name", cleaned.get("event"))
                cleaned.setdefault("scheduled_at", cleaned.get("release_time_utc") or cleaned.get("timestamp"))
                cleaned.setdefault("consensus", cleaned.get("forecast"))
                cleaned.setdefault("source_timestamp", cleaned.get("retrieved_at_utc") or cleaned.get("timestamp"))
                scheduled_at = cleaned.get("scheduled_at")
                actual = cleaned.get("actual")
                if actual is not None:
                    cleaned.setdefault("calendar_status", CalendarEventStatus.RELEASED)
                elif scheduled_at is not None:
                    scheduled_dt = scheduled_at if scheduled_at.tzinfo else scheduled_at.replace(tzinfo=UTC)
                    cleaned.setdefault(
                        "calendar_status",
                        CalendarEventStatus.UPCOMING if scheduled_dt >= now else CalendarEventStatus.UNKNOWN,
                    )
                items.append(EconomicEvent.model_validate(cleaned))
            except Exception:
                continue

        provider_result = None
        finance_result = None
        if effective_mode in {"today", "upcoming"}:
            provider_start = calendar_now.date().isoformat()
            provider_end = (
                calendar_now.date() if effective_mode == "today"
                else calendar_now.date() + timedelta(days=30)
            ).isoformat()
            settings = self.manager.settings
            finance_result = await FinanceCalendarProvider(
                base_url=settings.financecalendar_base_url,
                enabled=settings.financecalendar_enabled,
            ).fetch(
                mode="today" if effective_mode == "today" else "calendar",
                start=provider_start,
                end=provider_end,
            )
            items.extend(finance_result.events)
            # Trading Economics remains an optional backup, never a source of
            # stale records when the primary today request is unavailable.
            if finance_result.status == ProviderStatus.PROVIDER_UNAVAILABLE:
                provider_result = await TradingEconomicsProvider(self.manager.settings).fetch(
                    start=provider_start,
                    end=provider_end,
                )
                items.extend(provider_result.events)

        items = group_related_events(deduplicate_events(items))
        if effective_mode == "today":
            items = [
                item for item in items
                if item.timestamp >= day_start and item.timestamp < day_end
            ]
        if effective_mode == "released":
            items = [item for item in items if item.calendar_status == CalendarEventStatus.RELEASED]
        elif effective_mode == "unknown":
            items = [item for item in items if item.calendar_status == CalendarEventStatus.UNKNOWN]

        provider_names = sorted({item.provider or item.source or "unknown" for item in items})
        provider_statuses = {name: ProviderStatus.OK for name in provider_names}
        if finance_result is not None:
            provider_statuses[finance_result.provider] = finance_result.status
        if provider_result is not None:
            provider_statuses[provider_result.provider] = provider_result.status
        primary_result = finance_result or provider_result
        if effective_mode == "today" and not items:
            status = ProviderStatus.NO_DATA
        elif primary_result is not None and primary_result.status in {
            ProviderStatus.PROVIDER_UNAVAILABLE,
            ProviderStatus.NOT_CONFIGURED,
        } and not items:
            status = primary_result.status
        elif primary_result is not None and primary_result.status == ProviderStatus.PARTIAL_DATA:
            status = ProviderStatus.PARTIAL_DATA
        else:
            status = ProviderStatus.OK if items else ProviderStatus.NO_DATA
        analysis = None
        if include_analysis:
            from app.services.xauusd_event_intelligence import XAUUSDEventIntelligence
            analysis = XAUUSDEventIntelligence().analyze(items).__dict__
        return EconomicEventListResponse(
            items=items,
            generated_at=datetime.now(UTC),
            status=status,
            provider_statuses=provider_statuses,
            date=date or (calendar_now.date().isoformat() if effective_mode == "today" else None),
            timezone=timezone,
            analysis=analysis,
            attribution_url="https://www.financecalendar.com",
        )
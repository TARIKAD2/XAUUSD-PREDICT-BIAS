from datetime import UTC, datetime
from typing import Any
from collections import defaultdict
import hashlib

import httpx

from app.core.config import Settings
from app.schemas.economic import CalendarEventStatus, EconomicEvent, EventImportance, EventStatus


class EconomicNormalizationError(ValueError):
    pass


def _parse_optional_timestamp(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp.astimezone(UTC)


def normalize_event(raw: dict[str, Any], *, preserve_nullable_scheduled_at: bool = False) -> EconomicEvent:
    try:
        actual = float(raw["actual"]) if raw.get("actual") is not None and str(raw.get("actual")).strip() not in ("", "null", "None", "N/A") else None
        forecast = float(raw["forecast"]) if raw.get("forecast") is not None and str(raw.get("forecast")).strip() not in ("", "null", "None", "N/A") else None
        previous = float(raw["previous"]) if raw.get("previous") is not None and str(raw.get("previous")).strip() not in ("", "null", "None", "N/A") else None
        revision = float(raw["revision"]) if raw.get("revision") is not None and str(raw.get("revision")).strip() not in ("", "null", "None", "N/A") else None
        
        stamp = _parse_optional_timestamp(raw.get("timestamp")) or datetime.now(UTC)
        scheduled_at = _parse_optional_timestamp(raw.get("scheduled_at") or raw.get("release_time_utc"))
        if scheduled_at is None and not preserve_nullable_scheduled_at:
            scheduled_at = stamp
        surprise = actual - forecast if isinstance(actual, (int, float)) and isinstance(forecast, (int, float)) else None
        
        status = EventStatus.PUBLISHED if actual is not None else (EventStatus.SCHEDULED if raw.get("release_time_utc") or stamp >= datetime.now(UTC) else EventStatus.UNAVAILABLE)
        if raw.get("status"):
            try:
                status = EventStatus(str(raw["status"]))
            except ValueError:
                pass

        unit = str(raw.get("unit")) if raw.get("unit") is not None and str(raw.get("unit")).strip() not in ("", "null", "None") else None

        raw_importance = str(raw.get("importance", "medium")).lower()
        if raw_importance not in {member.value for member in EventImportance}:
            raw_importance = "medium"
        information_available_at = _parse_optional_timestamp(
            raw.get("information_available_at") or raw.get("actual_at") or raw.get("release_time_utc")
        )
        return EconomicEvent(
            event=str(raw["event"]),
            event_name=str(raw.get("event_name") or raw["event"]),
            country=(str(raw["country"]).upper() if raw.get("country") not in (None, "") else None),
            currency=(str(raw["currency"]).upper() if raw.get("currency") not in (None, "") else None),
            timestamp=stamp,
            scheduled_at=scheduled_at,
            actual=actual,
            forecast=forecast,
            consensus=forecast,
            previous=previous,
            revision=revision,
            surprise=surprise,
            importance=EventImportance(raw_importance),
            source=str(raw.get("source") or "unknown"),
            provider=str(raw.get("provider") or raw.get("source") or "unknown"),
            event_id=str(raw.get("event_id")) if raw.get("event_id") is not None else None,
            provider_event_id=str(raw.get("provider_event_id")) if raw.get("provider_event_id") is not None else None,
            indicator=str(raw.get("indicator")) if raw.get("indicator") is not None else str(raw["event"]),
            release_time_utc=_parse_optional_timestamp(raw.get("release_time_utc")),
            observation_period=str(raw.get("observation_period")) if raw.get("observation_period") is not None else None,
            revised_previous=float(raw["revised_previous"]) if raw.get("revised_previous") is not None and str(raw.get("revised_previous")).strip() not in ("", "null", "None") else None,
            unit=unit,
            retrieved_at_utc=_parse_optional_timestamp(raw.get("retrieved_at_utc")) or datetime.now(UTC),
            vintage_time_utc=_parse_optional_timestamp(raw.get("vintage_time_utc")),
            source_timestamp=_parse_optional_timestamp(raw.get("source_timestamp")) or scheduled_at,
            calendar_status=(
                CalendarEventStatus.RELEASED
                if actual is not None
                else CalendarEventStatus.UPCOMING
                if scheduled_at is not None and scheduled_at >= datetime.now(UTC)
                else CalendarEventStatus.UNKNOWN
            ),
            related_group=str(raw.get("related_group")) if raw.get("related_group") is not None else None,
            related_events=[str(value) for value in raw.get("related_events", []) if value],
            macro_theme=str(raw.get("macro_theme")) if raw.get("macro_theme") else None,
            status=status,
            information_available_at=information_available_at,
            source_url=str(raw["source_url"]) if raw.get("source_url") else None,
            all_day=raw.get("all_day") if isinstance(raw.get("all_day"), bool) else None,
            raw=raw.get("raw") if isinstance(raw.get("raw"), dict) else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EconomicNormalizationError("Invalid economic event.") from exc


def event_deduplication_key(event: EconomicEvent) -> tuple:
    """Return a stable identity across provider retries and equivalent payloads."""
    provider_id = event.provider_event_id or event.event_id
    if provider_id:
        return (event.provider or event.source, str(provider_id))
    return (
        event.event.strip().casefold(),
        event.country.upper() if event.country else "",
        event.currency.upper() if event.currency else "",
        event.scheduled_at or event.timestamp,
    )


def deduplicate_events(events: list[EconomicEvent]) -> list[EconomicEvent]:
    """Deduplicate deterministically, preferring the most complete/latest record."""
    selected: dict[tuple, EconomicEvent] = {}
    for event in events:
        key = event_deduplication_key(event)
        old = selected.get(key)
        if old is None:
            selected[key] = event
            continue
        old_score = sum(value is not None for value in old.model_dump().values())
        new_score = sum(value is not None for value in event.model_dump().values())
        if (new_score, event.retrieved_at_utc or datetime.min.replace(tzinfo=UTC)) > (
            old_score,
            old.retrieved_at_utc or datetime.min.replace(tzinfo=UTC),
        ):
            selected[key] = event
    return sorted(selected.values(), key=lambda item: (item.timestamp, item.event.casefold()))


def group_related_events(events: list[EconomicEvent]) -> list[EconomicEvent]:
    """Assign deterministic groups for known macro releases without changing identity."""
    grouped: dict[tuple, str] = {}
    members: dict[str, list[EconomicEvent]] = defaultdict(list)

    def theme_for(event: EconomicEvent) -> tuple[str | None, str | None]:
        name = event.event.casefold()
        if "cpi" in name or "consumer price" in name or "ppi" in name or "producer price" in name:
            return ("inflation", "inflation")
        if any(term in name for term in ("nonfarm", "payroll", "unemployment", "average hourly", "jobless")):
            return ("labor", "labor market")
        if "fomc" in name or "federal funds" in name or "interest rate" in name:
            return ("central-bank", "monetary policy")
        if "gdp" in name or "gross domestic" in name:
            return ("growth", "growth")
        if "retail sales" in name or "consumer activity" in name:
            return ("consumer", "consumer activity")
        return (None, None)

    result: list[EconomicEvent] = []
    for event in deduplicate_events(events):
        theme_key, theme = theme_for(event)
        if theme_key:
            basis = (
                event.country.upper() if event.country else "",
                event.currency.upper() if event.currency else "",
                theme_key,
                (event.scheduled_at or event.timestamp).date(),
            )
            if basis not in grouped:
                digest = hashlib.sha1("|".join(map(str, basis)).encode()).hexdigest()[:12]
                grouped[basis] = f"{event.country.lower()}-{theme_key}-{digest}"
            group = grouped[basis]
        else:
            group = event.related_group
        enriched = event.model_copy(update={"related_group": group, "macro_theme": event.macro_theme or theme})
        result.append(enriched)
        if group:
            members.setdefault(group, []).append(enriched)

    by_group = {key: [item.event_name or item.event for item in values] for key, values in members.items()}
    return [
        item.model_copy(update={
            "related_events": [name for name in by_group.get(item.related_group or "", []) if name != (item.event_name or item.event)]
        })
        for item in result
    ]


def _event(
    name: str,
    timestamp: datetime,
    actual: float | None,
    previous: float | None,
    importance: str,
    source: str,
    unit: str | None = None,
    forecast: float | None = None,
) -> EconomicEvent:
    return EconomicEvent(
        event=name,
        event_name=name,
        country="US",
        currency="USD",
        timestamp=timestamp,
        scheduled_at=timestamp,
        actual=actual,
        forecast=forecast,
        previous=previous,
        revision=None,
        surprise=actual - forecast if actual is not None and forecast is not None else None,
        importance=EventImportance(importance),
        source=source,
        provider=source,
        indicator=name,
        observation_period=timestamp.date().isoformat(),
        unit=unit,
        retrieved_at_utc=datetime.now(UTC),
        source_timestamp=timestamp,
        calendar_status=CalendarEventStatus.RELEASED if actual is not None else CalendarEventStatus.UNKNOWN,
        status=EventStatus.PUBLISHED if actual is not None else EventStatus.SCHEDULED,
    )


class FredCollector:
    """US economic observations from FRED. Forecast consensus is not provided by FRED."""

    SERIES_CONFIG = [
        {"id": "CPIAUCSL", "name": "US Consumer Price Index (CPI)", "importance": "high", "unit": "Index"},
        {"id": "PCEPI", "name": "US PCE Price Index", "importance": "high", "unit": "Index"},
        {"id": "UNRATE", "name": "US Unemployment Rate", "importance": "high", "unit": "%"},
        {"id": "PAYEMS", "name": "US Nonfarm Payrolls (NFP)", "importance": "high", "unit": "K"},
        {"id": "ICSA", "name": "US Initial Jobless Claims", "importance": "high", "unit": "Claims"},
        {"id": "FEDFUNDS", "name": "Federal Funds Effective Rate", "importance": "high", "unit": "%"},
        {"id": "GDP", "name": "US Gross Domestic Product (GDP)", "importance": "high", "unit": "B USD"},
        {"id": "RSXFS", "name": "US Retail Sales", "importance": "high", "unit": "M USD"},
        {"id": "PPIACO", "name": "US Producer Price Index (PPI)", "importance": "high", "unit": "Index"},
        {"id": "JTSJOL", "name": "US JOLTS Job Openings", "importance": "high", "unit": "K"},
        {"id": "ISM/MAN_PMI", "name": "ISM Manufacturing PMI", "importance": "high", "unit": "Index"},
    ]

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def fetch(self, limit: int = 5) -> list[EconomicEvent]:
        api_key = self._settings.fred_api_key or self._settings.economic_data_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise EconomicNormalizationError("FRED_API_KEY is not configured.")
        events: list[EconomicEvent] = []
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        try:
            for series in self.SERIES_CONFIG:
                params = {
                    "series_id": series["id"],
                    "api_key": api_key.get_secret_value(),
                    "file_type": "json",
                    "limit": limit,
                    "sort_order": "desc",
                }
                resp = await client.get("https://api.stlouisfed.org/fred/series/observations", params=params)
                if resp.status_code != 200:
                    continue
                observations = resp.json().get("observations", [])
                for index, observation in enumerate(observations):
                    try:
                        actual = float(observation.get("value"))
                    except (TypeError, ValueError):
                        continue
                    dt_str = observation.get("date")
                    if not dt_str:
                        continue
                    timestamp = datetime.fromisoformat(f"{dt_str}T00:00:00+00:00")
                    previous = None
                    if index + 1 < len(observations):
                        try:
                            previous = float(observations[index + 1].get("value"))
                        except (TypeError, ValueError):
                            previous = None
                    events.append(
                        _event(
                            series["name"],
                            timestamp,
                            actual,
                            previous,
                            series["importance"],
                            "FRED",
                            unit=series.get("unit"),
                            forecast=None,
                        )
                    )
        finally:
            if owns_client:
                await client.aclose()
        return sorted(events, key=lambda item: item.timestamp, reverse=True)


class BlsCollector:
    """BLS published labor/price series. Forecast consensus is not provided by BLS."""

    SERIES = [
        {"id": "CUSR0000SA0", "name": "US CPI (BLS)", "importance": "high", "unit": "Index"},
        {"id": "CES0000000001", "name": "US Nonfarm Payrolls (BLS)", "importance": "high", "unit": "K"},
        {"id": "LNS14000000", "name": "US Unemployment Rate (BLS)", "importance": "high", "unit": "%"},
        {"id": "PRS85006092", "name": "US Labor Productivity", "importance": "medium", "unit": "%"},
    ]

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def fetch(self, years: int = 2) -> list[EconomicEvent]:
        api_key = self._settings.bls_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise EconomicNormalizationError("BLS_API_KEY is not configured.")
        payload = {
            "seriesid": [item["id"] for item in self.SERIES],
            "registrationkey": api_key.get_secret_value(),
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        try:
            response = await client.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise EconomicNormalizationError("BLS request failed.") from exc
        finally:
            if owns_client:
                await client.aclose()
        lookup = {item["id"]: item for item in self.SERIES}
        events: list[EconomicEvent] = []
        for series in body.get("Results", {}).get("series", []):
            meta = lookup.get(series.get("seriesID"))
            if not meta:
                continue
            rows = series.get("data") or []
            for index, row in enumerate(rows[:8]):
                try:
                    actual = float(str(row.get("value")).replace(",", ""))
                except (TypeError, ValueError):
                    continue
                period = str(row.get("period") or "")
                year = str(row.get("year") or "")
                if period.startswith("M") and year:
                    month = int(period[1:])
                    timestamp = datetime(int(year), month, 1, tzinfo=UTC)
                elif period.startswith("Q") and year:
                    month = int(period[1:]) * 3
                    timestamp = datetime(int(year), month, 1, tzinfo=UTC)
                else:
                    continue
                previous = None
                if index + 1 < len(rows):
                    try:
                        previous = float(str(rows[index + 1].get("value")).replace(",", ""))
                    except (TypeError, ValueError):
                        previous = None
                events.append(
                    _event(
                        meta["name"],
                        timestamp,
                        actual,
                        previous,
                        meta["importance"],
                        "BLS",
                        unit=meta.get("unit"),
                        forecast=None,
                    )
                )
        return events


class BeaCollector:
    """BEA NIPA GDP observations. Forecast consensus is not provided by BEA."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client

    async def fetch(self) -> list[EconomicEvent]:
        api_key = self._settings.bea_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            raise EconomicNormalizationError("BEA_API_KEY is not configured.")
        params = {
            "UserID": api_key.get_secret_value(),
            "method": "GetData",
            "DataSetName": "NIPA",
            "TableName": "T10101",
            "Frequency": "Q",
            "Year": "LAST5",
            "ResultFormat": "JSON",
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._settings.request_timeout_seconds)
        try:
            response = await client.get("https://apps.bea.gov/api/data/", params=params)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise EconomicNormalizationError("BEA request failed.") from exc
        finally:
            if owns_client:
                await client.aclose()
        data = body.get("BEAAPI", {}).get("Results", {}).get("Data", [])
        gdp_rows = [row for row in data if str(row.get("LineDescription", "")).lower() == "gross domestic product"]
        events: list[EconomicEvent] = []
        for index, row in enumerate(gdp_rows[:12]):
            try:
                actual = float(str(row.get("DataValue")).replace(",", ""))
            except (TypeError, ValueError):
                continue
            time_period = str(row.get("TimePeriod") or "")
            if len(time_period) < 6 or "Q" not in time_period:
                continue
            year = int(time_period[:4])
            quarter = int(time_period[-1])
            timestamp = datetime(year, quarter * 3, 1, tzinfo=UTC)
            previous = None
            if index + 1 < len(gdp_rows):
                try:
                    previous = float(str(gdp_rows[index + 1].get("DataValue")).replace(",", ""))
                except (TypeError, ValueError):
                    previous = None
            events.append(_event("US GDP (BEA)", timestamp, actual, previous, "high", "BEA", unit="B USD", forecast=None))
        return events

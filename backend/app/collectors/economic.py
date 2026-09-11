from datetime import UTC,datetime
from app.schemas.economic import EconomicEvent,EventImportance
class EconomicNormalizationError(ValueError): pass
def normalize_event(raw):
    try:
        actual=float(raw["actual"]) if raw.get("actual") is not None else None; forecast=float(raw["forecast"]) if raw.get("forecast") is not None else None; stamp=datetime.fromisoformat(str(raw["timestamp"]).replace("Z","+00:00")); stamp=stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp.astimezone(UTC); return EconomicEvent(event=str(raw["event"]),country=str(raw["country"]).upper(),currency=str(raw["currency"]).upper(),timestamp=stamp,actual=actual,forecast=forecast,surprise=actual-forecast if actual is not None and forecast is not None else None,importance=EventImportance(raw.get("importance","medium")))
    except (KeyError,TypeError,ValueError) as e: raise EconomicNormalizationError("Invalid economic event.") from e

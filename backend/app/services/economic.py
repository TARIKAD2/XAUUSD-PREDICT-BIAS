"""Economic-calendar persistence and retrieval."""
from datetime import UTC,datetime
from app.collectors.economic import normalize_event
from app.db.client import MongoClientManager
from app.db.collections import ECONOMIC_EVENTS
from app.db.repositories import MongoRepository
from app.schemas.economic import EconomicEvent,EconomicEventListResponse
class EconomicDataUnavailableError(RuntimeError):pass
class EconomicService:
 def __init__(self,manager:MongoClientManager):self.manager=manager;self.repo=MongoRepository(manager,ECONOMIC_EVENTS)
 async def upsert_raw(self,raw:dict)->EconomicEvent:
  event=normalize_event(raw);doc=event.model_dump(mode="python")|{"ingested_at":datetime.now(UTC)};await self.repo.upsert_one({"event":event.event,"country":event.country,"currency":event.currency,"timestamp":event.timestamp},doc);return event
 async def list(self,limit:int)->EconomicEventListResponse:
  if not self.manager.is_connected:raise EconomicDataUnavailableError("Economic-event storage is unavailable.")
  docs=await self.repo.find_recent({},limit)
  if not docs:raise EconomicDataUnavailableError("No verified economic events are available.")
  return EconomicEventListResponse(items=[EconomicEvent.model_validate(d) for d in docs],generated_at=datetime.now(UTC))
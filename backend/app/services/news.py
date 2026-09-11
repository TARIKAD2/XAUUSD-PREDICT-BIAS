from datetime import UTC,datetime
from app.db.client import MongoClientManager
from app.db.collections import NEWS
from app.db.repositories import MongoRepository
from app.schemas.news import NewsItem,NewsListResponse
class NewsUnavailableError(RuntimeError): pass
class NewsService:
 def __init__(self,m:MongoClientManager): self.r=MongoRepository(m,NEWS);self.m=m
 async def save(self,items:list[NewsItem])->int:
  for i in items: await self.r.upsert_one({"url":str(i.url)},i.model_dump(mode="python")|{"ingested_at":datetime.now(UTC)})
  return len(items)
 async def list(self,limit:int)->NewsListResponse:
  if not self.m.is_connected: raise NewsUnavailableError("News storage is unavailable.")
  docs=await self.r.find_recent({},limit)
  if not docs: raise NewsUnavailableError("No verified news is available.")
  return NewsListResponse(items=[NewsItem.model_validate(d) for d in docs],generated_at=datetime.now(UTC))
"""Compliant RSS ingestion and deterministic, evidence-bearing news enrichment."""
from __future__ import annotations
import re
from datetime import UTC,datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree
import httpx
from app.schemas.market import AssetSymbol
from app.schemas.news import MarketImpact,NewsCategory,NewsImportance,NewsItem,NewsSentiment
POSITIVE={"rally","rallies","gain","gains","eases","easing","dovish","beat","beats"};NEGATIVE={"loss","losses","decline","declines","hawkish","miss","misses","recession","war"}
def classify(text:str):
 tokens=set(re.findall(r"[a-z]+",text.lower()));score=len(tokens&POSITIVE)-len(tokens&NEGATIVE);sentiment=NewsSentiment.POSITIVE if score>0 else NewsSentiment.NEGATIVE if score<0 else NewsSentiment.NEUTRAL
 category=NewsCategory.MONETARY_POLICY if tokens&{"fed","ecb","boj","boe","fomc","rate"} else NewsCategory.MACRO if tokens&{"cpi","gdp","employment","nfp","pce"} else NewsCategory.COMMODITIES if "gold" in tokens else NewsCategory.GEOPOLITICS if tokens&{"war","sanction"} else NewsCategory.MARKET
 symbols=[s for s in AssetSymbol if s.value.lower() in text.lower()]; symbols += [AssetSymbol.XAUUSD] if "gold" in tokens and AssetSymbol.XAUUSD not in symbols else []
 importance=NewsImportance.HIGH if category in {NewsCategory.MACRO,NewsCategory.MONETARY_POLICY} else NewsImportance.MEDIUM if symbols else NewsImportance.LOW
 impacts=[MarketImpact(asset=s,direction=sentiment,rationale="Lexicon classification from the published title and description.") for s in symbols]
 return sentiment,category,importance,symbols,impacts
class NewsCollectionError(RuntimeError):pass
def normalize_rss(xml:bytes,source:str)->list[NewsItem]:
 try:root=ElementTree.fromstring(xml)
 except ElementTree.ParseError as e:raise NewsCollectionError("RSS feed is malformed.") from e
 out=[]
 for entry in root.findall(".//item"):
  title=(entry.findtext("title")or"").strip();url=(entry.findtext("link")or"").strip()
  if not title or not url:continue
  desc=(entry.findtext("description")or"").strip()or None;raw=entry.findtext("pubDate")
  try:published=parsedate_to_datetime(raw).astimezone(UTC) if raw else datetime.now(UTC)
  except (TypeError,ValueError):published=datetime.now(UTC)
  sentiment,category,importance,symbols,impacts=classify(f"{title} {desc or ''}");out.append(NewsItem(title=title,description=desc,source=source,url=url,published_at=published,symbols=symbols,category=category,sentiment=sentiment,importance=importance,impacts=impacts))
 return out
class RssCollector:
 def __init__(self,timeout:int=15):self.timeout=timeout
 async def fetch(self,url:str,source:str)->list[NewsItem]:
  async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True) as c:
   try:r=await c.get(url,headers={"User-Agent":"AI-Market-Intelligence/0.1 (+research)"});r.raise_for_status()
   except httpx.HTTPError as e:raise NewsCollectionError("RSS request failed.") from e
  return normalize_rss(r.content,source)
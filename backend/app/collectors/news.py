"""RSS news collection and transparent rule-based normalization."""
from __future__ import annotations
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree
import re
import httpx
from app.schemas.market import AssetSymbol
from app.schemas.news import NewsImportance, NewsItem, NewsSentiment

POSITIVE={"beat","eases","decline","falls","dovish","growth","rally","gain"}; NEGATIVE={"miss","rises","surge","hawkish","recession","war","fall","loss"}
class NewsCollectionError(RuntimeError): pass

def classify(text:str)->tuple[NewsSentiment,NewsImportance,list[AssetSymbol]]:
 lowered=text.lower(); tokens=set(re.findall(r"[a-z]+", lowered)); score=len(tokens & POSITIVE)-len(tokens & NEGATIVE)
 sentiment=NewsSentiment.POSITIVE if score>0 else NewsSentiment.NEGATIVE if score<0 else NewsSentiment.NEUTRAL
 symbols=[s for s in AssetSymbol if s.value.lower() in lowered or (s==AssetSymbol.XAUUSD and "gold" in lowered)]
 importance=NewsImportance.HIGH if any(x in lowered for x in ("cpi","fomc","nfp","interest rate","gdp")) else NewsImportance.MEDIUM if symbols else NewsImportance.LOW
 return sentiment,importance,symbols

def normalize_rss(xml:bytes,source:str)->list[NewsItem]:
 try: root=ElementTree.fromstring(xml)
 except ElementTree.ParseError as e: raise NewsCollectionError("RSS feed is malformed.") from e
 items=[]
 for entry in root.findall('.//item'):
  title=(entry.findtext('title') or '').strip(); link=(entry.findtext('link') or '').strip()
  if not title or not link: continue
  description=(entry.findtext('description') or '').strip() or None; raw_date=entry.findtext('pubDate')
  try: published=parsedate_to_datetime(raw_date).astimezone(UTC) if raw_date else datetime.now(UTC)
  except (TypeError,ValueError): published=datetime.now(UTC)
  sentiment,importance,symbols=classify(f"{title} {description or ''}")
  items.append(NewsItem(title=title,description=description,source=source,url=link,published_at=published,symbols=symbols,sentiment=sentiment,importance=importance))
 return items

class RssCollector:
 def __init__(self,timeout:int=15): self.timeout=timeout
 async def fetch(self,url:str,source:str)->list[NewsItem]:
  async with httpx.AsyncClient(timeout=self.timeout,follow_redirects=True) as c:
   try: r=await c.get(url,headers={"User-Agent":"AI-Market-Intelligence/0.1 (+research)"}); r.raise_for_status()
   except httpx.HTTPError as e: raise NewsCollectionError("RSS request failed.") from e
  return normalize_rss(r.content,source)
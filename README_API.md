# API Research — AI Market Intelligence

Researched 2026-09-11 from current official provider documentation/pricing. This is a zero-budget educational/research recommendation, not a guarantee of vendor availability. Verify symbols using each vendor’s reference/search endpoint before enabling collectors.

## Decision: use multiple providers

```text
Twelve Data (eligible FX) + Marketaux (financial news) + FRED/ALFRED + BLS + BEA (US macro)
```

No researched free provider offers deep 1-minute history for all six assets, financial news, and a historical consensus/actual/revision calendar. Do not force one provider.

## Detailed comparison

Legend: ✅ documented support; ⚠️ limited/plan-dependent; ❌ not supplied; ? exact entitlement or symbol not verified publicly.

| Provider | Market | News | Calendar | XAUUSD | US100 | EURUSD | DXY | GBPUSD | USDJPY | Historical/intraday | Free limit | Key | Best use |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [Twelve Data](https://twelvedata.com/pricing) | ✅ | ❌ | ❌ | ⚠️ `XAU/USD`; commodity access not Basic | ? | ✅ `EUR/USD` | ? | ✅ `GBP/USD` | ✅ `USD/JPY` | FX intraday; commodity/deep-history plan-dependent | 8 credits/min, 800/day | ✅ | Primary FX refresh |
| [Alpha Vantage](https://www.alphavantage.co/documentation/) | ⚠️ | ✅ | ⚠️ economic indicators, not consensus calendar | ⚠️ `GOLD_SILVER_SPOT`/history, not XAUUSD candles | ⚠️ index history premium | ✅ `EUR`/`USD` | ? | ✅ `GBP`/`USD` | ✅ `USD`/`JPY` | FX intraday premium | 25/day | ✅ | Low-volume backup/research |
| [Finnhub](https://finnhub.io/docs/api/quote) | ⚠️ | ✅ | ⚠️ premium | ? | ? | ⚠️ | ? | ⚠️ | ⚠️ | Free news one year; calendar premium | endpoint dependent | ✅ | News backup only |
| [FMP](https://intelligence.financialmodelingprep.com/developer/docs/stable/financial-symbols-list) | ⚠️ | ⚠️ | ⚠️ | ? | ? | ? | ? | ? | ? | Entitlements/symbols require account verification | ⚠️ | ✅ | Evaluate later only |
| [Marketstack](https://marketstack.com/pricing) | ⚠️ | ❌ | ❌ | ? | ⚠️ paid | ? | ? | ? | ? | Free EOD, 1-year; no free intraday | 100/month | ✅ | Not suitable primary |
| [Marketaux](https://www.marketaux.com/pricing) | ❌ | ✅ | ❌ | ⚠️ entity relevance | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | Instant news; 3 articles/request | 100/day | ✅ | **Primary free financial news** |
| [GNews](https://gnews.io/pricing) | ❌ | ⚠️ | ❌ | ⚠️ keyword | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | 12-hour delay, 30-day history | 100/day, dev/test/non-commercial | ✅ | General-news supplement |
| [NewsAPI](https://newsapi.org/pricing) | ❌ | ⚠️ | ❌ | ⚠️ keyword | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | 24-hour delay, one month | 100/day, development only | ✅ | Local development only |
| [FRED / ALFRED](https://fred.stlouisfed.org/docs/api/fred/) | ❌ | ❌ | ⚠️ releases and observations, not consensus | ❌ | ❌ | ❌ | ⚠️ series must be verified | ❌ | ❌ | Deep history, release dates, vintage data | API key | ✅ | **Primary macro history/revisions** |
| [BLS](https://www.bls.gov/developers/api_faqs.htm) | ❌ | ❌ | ⚠️ published US data, not consensus | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Up to 20 years/query registered v2 | 500/day registered | ⚠️ | CPI, payrolls, unemployment |
| [BEA](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf) | ❌ | ❌ | ⚠️ published US data, not consensus | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Historical published data | API user ID | ✅ | GDP/PCE |

### Verified vendor formats

- Twelve Data publicly documents `XAU/USD`, `EUR/USD`, `GBP/USD`, `USD/JPY`. Do not send internal symbols such as `XAUUSD` to it.
- Alpha Vantage documents pairs as `from_symbol=EUR&to_symbol=USD`; its `FX_INTRADAY` endpoint is premium.
- `NDX` and `DXY` access/entitlement must be verified through the provider instrument search—this document does not assume them.

## Scores / 10

| Provider | Score | Reason |
|---|---:|---|
| FRED + ALFRED | 9.0 | Historical macro, release and vintage support; no candles/consensus. |
| BLS + BEA | 8.5 | Authoritative source statistics; no forecast consensus. |
| Marketaux | 7.5 | Immediate financial news, 100/day, entity metadata. |
| Twelve Data | 7.0 | Strong free FX refresh; Basic excludes commodities. |
| Alpha Vantage | 5.5 | Broad but 25/day and required intraday/index functions premium. |
| Finnhub | 5.0 | News useful; calendar premium. |
| GNews | 4.0 | Delayed, short history, dev/test free plan. |
| NewsAPI | 3.5 | Development-only free licence. |
| Marketstack | 2.0 | Free tier lacks useful history/intraday. |
| FMP | ? | Do not score until exact free account entitlement is checked. |

## Request math and caching

Six markets × four timeframes = 24 series.

- 15-minute polling: `24 × 96 = 2,304` requests/day.
- Hourly polling: `24 × 24 = 576` requests/day.
- One daily refresh: 24/day.
- Five news queries every 30 minutes: 240/day.

Therefore Twelve Data free 800/day cannot support 15-minute polling of 24 independent series plus backfill; Marketaux free 100/day cannot support 30-minute polling of five feeds. Alpha Vantage free 25/day is not a primary feed.

Cache strategy:

1. Backfill each date range once; store raw payload and normalized candles/events.
2. Store vendor symbol, provider, retrieval timestamp, UTC source timestamp and content hash.
3. Refresh finalised 15m/1h candles at most hourly; 4h/daily after close.
4. Deduplicate news by Marketaux UUID/URL; poll every 30–60 minutes within quota.
5. Refresh FRED/BLS/BEA after release windows or daily, never from dashboard requests.
6. Retain a cursor/watermark for every query and use exponential backoff on rate limits.

## Economic event-reaction research

For “XAUUSD after CPI over ten years”, use official BLS/FRED release dates and actual/revised data; use ALFRED vintages for what was known historically. Join UTC event timestamps to stored candles and calculate +5m, +15m, +30m, +1h, +4h, +1d returns. Exclude missing release-time/candle cases and report sample size.

FRED/BLS/BEA do **not** supply market consensus forecasts. Only calculate `actual - forecast` when a separately licensed consensus source provides both values; otherwise store `surprise=null`, not an invented value.

## Recommended architecture

```text
Twelve Data FX       Marketaux news       FRED / BLS / BEA macro
       |                    |                      |
       +--------------------+----------------------+
                            |
              Collector -> validation -> raw archive
                            |
       normalized PostgreSQL/MongoDB -> leakage-safe features
                            |
       chronological XGBoost / LightGBM -> SHAP -> FastAPI -> Next.js
```

Use PostgreSQL for candle/event/reaction joins and analytical queries when introduced. The current MongoDB architecture remains appropriate for raw JSON, news and application documents; do not duplicate every collection until PostgreSQL is justified.

## Accounts to create

1. [Twelve Data](https://twelvedata.com/pricing) — validate every required symbol first.
2. [Marketaux](https://www.marketaux.com/pricing) — primary financial news.
3. [FRED](https://fred.stlouisfed.org/docs/api/fred/) — macro/revisions.
4. [BLS](https://www.bls.gov/developers/api_faqs.htm) — register for v2 limits.
5. [BEA](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf) — GDP/PCE.
6. [Alpha Vantage](https://www.alphavantage.co/documentation/) — optional backup only.

Do not create Finnhub, Marketstack, GNews or NewsAPI accounts unless a confirmed gap remains. Verified students may consider [GNews education access](https://gnews.io/student-education).

## `.env` and security

```env
MARKET_DATA_PROVIDER=twelve_data
MARKET_DATA_API_KEY=

NEWS_PROVIDER=marketaux
NEWS_API_KEY=

ECONOMIC_CALENDAR_PROVIDER=fred_bls_bea
FRED_API_KEY=
BLS_API_KEY=
BEA_API_KEY=

MONGODB_URI=
DATABASE_NAME=ai_market_intelligence
```

Only backend collectors read keys. Never use `NEXT_PUBLIC_` for a secret, place keys in React, commit `.env`, include it in an image, or expose it in an error/log. Browser -> FastAPI -> provider is the only permitted flow. Rotate a key if it is ever exposed.

## Final answers

### A. Best free market-data API

**Twelve Data**, for eligible FX pairs, because its Basic plan documents 800 daily credits and real-time forex. It is not a complete six-market answer: validate US100/DXY and do not assume free XAUUSD commodity access.

### B. Best free news API

**Marketaux**, because its free plan documents 100 daily requests, instant financial news, entity metadata and no payment details; cache because it returns only three articles/request.

### C. Best free economic calendar API

**FRED + BLS + BEA**, as a combined authoritative economic-history source. It is not a full forecast calendar: consensus/forecast fields remain unavailable without a licensed provider.

### D. Best backup API

**Alpha Vantage**, strictly low-volume fallback/research. Its free quota and premium FX intraday make it unsuitable as primary.

### E. Accounts required

Twelve Data, Marketaux, FRED, BLS, BEA; Alpha Vantage optional.

### F. Exact environment variables

Use the `.env` block above. Add none to frontend public variables except `NEXT_PUBLIC_API_URL`.

### G. What not to use

Do not use Marketstack as ML/backtesting primary, NewsAPI/GNews free plans for deployed production use, Finnhub free for calendar, or a single provider for all sources.

### H. Final recommendation

Start with **Twelve Data + Marketaux + FRED/BLS/BEA**, cache aggressively, validate symbols before ingestion, and show `NO_DATA`/`NOT_CONFIGURED` for gaps. This is the clearest defensible zero-budget architecture.
# AI Market Intelligence

A portable, research-only market intelligence platform for XAUUSD. It provides probabilistic analysis when real, validated data and trained models are available. It does not execute trades, guarantee returns, or fabricate predictions.

## Rapport PFA

Le rapport technique en français, basé sur l’architecture actuelle du dépôt, est disponible dans [README_RAPPORT_PFA.md](README_RAPPORT_PFA.md).

## Architecture

External market/news/economic sources are normalized by collectors, stored in MongoDB, turned into leakage-safe features, evaluated with chronological ML workflows, and exposed by FastAPI to a Next.js dashboard. See `PROJECT_ARCHITECTURE.md`.

## Environment

Copy `.env.example` to `.env`; never commit it.

- `MONGODB_URI`, `DATABASE_NAME`: MongoDB Atlas connection (`ai_market_intelligence`).
- `TWELVE_DATA_API_KEY`: Twelve Data market collection.
- `MARKETAUX_API_KEY` or `NEWS_API_KEY`: financial news.
- `FRED_API_KEY`, `BLS_API_KEY`, `BEA_API_KEY`: published US statistics (no consensus forecasts).
- `NEXT_PUBLIC_API_URL`: FastAPI origin used by the dashboard.
- `API_CORS_ORIGINS`: comma-separated frontend origins.

## Local development

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
Set-Location ..\frontend
npm install
npm run dev
```

Backend API docs: `http://localhost:8000/docs`.

## Ingestion

```powershell
.\.venv\Scripts\python.exe scripts\ingest_all_markets.py
.\.venv\Scripts\python.exe scripts\ingest_news.py
.\.venv\Scripts\python.exe scripts\ingest_economic.py
```

Market candles are upserted into `market_data` only.

## Tests and build

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..\frontend
npm run build
```

## Docker

Start Docker Desktop, then run `docker compose up --build`. `.env` is optional for booting the API, but live storage/collectors need the relevant credentials. Pass `NEXT_PUBLIC_API_URL` as a frontend build arg for a non-local API.

## Deployment

1. MongoDB Atlas: create a least-privilege database user and network access rule; copy its URI only to deployment secrets.
2. Railway: deploy `backend`, build with `pip install -r requirements.txt`, start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; set `MONGODB_URI`, `DATABASE_NAME`, and production `API_CORS_ORIGINS`.
3. Vercel: deploy `frontend`; set `NEXT_PUBLIC_API_URL` to the Railway HTTPS URL; run `npm run build`.
4. Confirm Railway `/api/health` and browser CORS before exposing the dashboard.

## API

- `GET /api/health`
- `GET /api/market`, `GET /api/market/{symbol}`
- `GET /api/news`
- `GET /api/economic-events`
- `GET /api/predictions`, `GET /api/predictions/{symbol}`
- `GET /api/model-performance`
- `GET /api/data-quality`
- `GET /api/explanations/{symbol}`

Missing data or untrained models return HTTP 503 with a clear `MODEL_NOT_READY` / unavailable message. Values are never invented.

## Model status

Training, calibration, walk-forward utilities, and SHAP helpers are implemented. The API serves predictions only when a trained `models/{symbol}_model.joblib` artifact exists. If no model has been trained against stored market data, the API reports MODEL_NOT_READY.

# AI Market Intelligence

A portable, research-only market intelligence platform for XAUUSD, US100, EURUSD, DXY, GBPUSD, and USDJPY. It provides probabilistic analysis when real, validated data and trained models are available. It does not execute trades, guarantee returns, or fabricate predictions.

## Architecture

External market/news/economic sources are normalized by collectors, stored in MongoDB, turned into leakage-safe features, evaluated with chronological ML workflows, and exposed by FastAPI to a Next.js dashboard. See `PROJECT_ARCHITECTURE.md`.

## Environment

Copy `.env.example` to `.env`; never commit it.

- `MONGODB_URI`, `DATABASE_NAME`: MongoDB Atlas connection.
- `MARKET_DATA_API_KEY`: Twelve Data market collection.
- `NEWS_API_KEY`, `ECONOMIC_DATA_API_KEY`: reserved provider credentials.
- `NEXT_PUBLIC_API_URL`: deployed FastAPI URL for the frontend.
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

## Tests and build

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..\frontend
npm run build
```

## Docker

Start Docker Desktop, then run `docker compose up --build`. `.env` is optional for booting the API, but live storage/collectors need the relevant credentials.

## Deployment

1. MongoDB Atlas: create a least-privilege database user and network access rule; copy its URI only to deployment secrets.
2. Railway: deploy `backend`, build with `pip install -r requirements.txt`, start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; set `MONGODB_URI`, `DATABASE_NAME`, and production `API_CORS_ORIGINS`.
3. Vercel: deploy `frontend`; set `NEXT_PUBLIC_API_URL` to the Railway HTTPS URL; run `npm run build`.
4. Confirm Railway `/api/health` and browser CORS before exposing the dashboard.

## Model status

Baseline chronological Logistic Regression and Random Forest tooling is present. Advanced XGBoost/LightGBM/SHAP requires successful optional installation; no model outputs are served until a real trained model and verified data are registered.
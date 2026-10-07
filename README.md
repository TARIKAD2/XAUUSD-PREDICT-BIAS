# 🏆 AI Market Intelligence — XAUUSD Prediction Platform

> **A portable, research-only market intelligence platform for XAUUSD (Gold/USD).** It provides probabilistic analysis when real, validated data and trained models are available. It does **not** execute trades, guarantee returns, or fabricate predictions.

---

## 📑 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start (TL;DR)](#-quick-start-tldr)
- [Detailed Setup](#-detailed-setup)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Environment Variables](#2-environment-variables)
  - [3. Backend Setup (Python / FastAPI)](#3-backend-setup-python--fastapi)
  - [4. Frontend Setup (Next.js)](#4-frontend-setup-nextjs)
- [Running with Docker](#-running-with-docker)
- [Data Ingestion](#-data-ingestion)
- [Model Training](#-model-training)
- [Testing](#-testing)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Rapport PFA (FR)](#-rapport-pfa-fr)
- [License](#-license)

---

## 🏗 Architecture Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   External APIs  │────▶│  FastAPI Backend  │◀───▶│  MongoDB Atlas   │
│                  │     │  (Python 3.13+)   │     │                  │
│ • Twelve Data    │     │                   │     │ • market_data    │
│ • Marketaux      │     │ • Collectors      │     │ • news           │
│ • FRED/BLS/BEA   │     │ • ML Pipeline     │     │ • economic_events│
└──────────────────┘     │ • REST API        │     │ • model_perf     │
                         └────────┬─────────┘     └──────────────────┘
                                  │
                                  │ HTTP (port 8000)
                                  │
                         ┌────────▼─────────┐
                         │  Next.js Frontend │
                         │  (React 19)       │
                         │  Port 3000        │
                         │                   │
                         │ • Dashboard       │
                         │ • War Room        │
                         │ • Charts & Gauges │
                         └──────────────────┘
```

External market/news/economic sources are normalized by **collectors**, stored in **MongoDB**, turned into leakage-safe features, evaluated with **chronological ML workflows**, and exposed by **FastAPI** to a **Next.js** dashboard. See [`PROJECT_ARCHITECTURE.md`](PROJECT_ARCHITECTURE.md) for details.

---

## 🛠 Tech Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| **Backend** | Python 3.13+, FastAPI, Uvicorn, Pydantic            |
| **Database**| MongoDB Atlas (via PyMongo / Motor)                  |
| **ML**      | scikit-learn, XGBoost, LightGBM, SHAP, NumPy, Pandas|
| **Frontend**| Next.js 15, React 19, Vanilla CSS                   |
| **DevOps**  | Docker, Docker Compose, Railway, Vercel              |
| **i18n**    | English 🇬🇧, French 🇫🇷, Arabic 🇲🇦                     |

---

## ✅ Prerequisites

Before you begin, make sure you have:

| Tool           | Minimum Version | Check Command       |
|----------------|-----------------|----------------------|
| **Python**     | 3.13+           | `python --version`   |
| **Node.js**    | 18+             | `node --version`     |
| **npm**        | 9+              | `npm --version`      |
| **Git**        | 2.x             | `git --version`      |
| **MongoDB Atlas** | Free tier (M0) | [atlas.mongodb.com](https://cloud.mongodb.com) |

**Optional:**
- Docker Desktop (for containerized deployment)
- API Keys: Twelve Data, Marketaux, FRED, BLS, BEA (for live data ingestion)

---

## ⚡ Quick Start (TL;DR)

```powershell
# 1. Clone
git clone https://github.com/YOUR_USERNAME/AI_XAUUSD.git
cd AI_XAUUSD

# 2. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 3. Create Python virtual environment & install backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

# 4. Start backend (Terminal 1)
cd backend
python -m uvicorn app.main:app --reload
# ➜ Backend running at http://localhost:8000

# 5. Start frontend (Terminal 2)
cd frontend
npm install
npm run dev
# ➜ Frontend running at http://localhost:3000
```

Open **http://localhost:3000** in your browser 🚀

---

## 📋 Detailed Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/YOUR_USERNAME/AI_XAUUSD.git
cd AI_XAUUSD
```

### 2. Environment Variables

Copy the example file and fill in your credentials:

```powershell
cp .env.example .env
```

Open `.env` in your editor and configure:

| Variable                     | Required | Description                                     |
|------------------------------|----------|-------------------------------------------------|
| `MONGODB_URI`                | ✅       | MongoDB Atlas connection string                 |
| `DATABASE_NAME`              | ✅       | Database name (default: `ai_market_intelligence`)|
| `TWELVE_DATA_API_KEY`        | ⬡        | Market OHLC data (for ingestion)                |
| `MARKETAUX_API_KEY`          | ⬡        | Financial news (for ingestion)                  |
| `FRED_API_KEY`               | ⬡        | US Federal Reserve economic data                |
| `BLS_API_KEY`                | ⬡        | US Bureau of Labor Statistics                   |
| `BEA_API_KEY`                | ⬡        | US Bureau of Economic Analysis                  |
| `EODHD_API_KEY`              | ⬡        | End of Day Historical Data                      |
| `ALPHAVANTAGE_API_KEY`       | ⬡        | Alpha Vantage market data                       |
| `FINNHUB_API_KEY`            | ⬡        | Finnhub financial data                          |
| `NEXT_PUBLIC_API_URL`        | ✅       | Backend URL (default: `http://localhost:8000`)   |
| `API_CORS_ORIGINS`           | ✅       | Frontend URL (default: `http://localhost:3000`)  |
| `MARKET_INGESTION_ENABLED`   | —        | Enable auto-ingestion (default: `false`)        |

> **⚠️ Never commit `.env` — it's in `.gitignore`.**

### 3. Backend Setup (Python / FastAPI)

```powershell
# Create virtual environment (one-time)
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1          # PowerShell (Windows)
# source .venv/bin/activate            # Bash (Linux/Mac)

# Install dependencies
pip install -r backend\requirements.txt

# Start the backend server
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Backend will be available at:** http://localhost:8000  
📄 **Interactive API docs:** http://localhost:8000/docs  
📄 **ReDoc docs:** http://localhost:8000/redoc

### 4. Frontend Setup (Next.js)

Open a **new terminal** window:

```powershell
cd frontend

# Install Node.js dependencies (one-time)
npm install

# Start the development server
npm run dev
```

✅ **Frontend will be available at:** http://localhost:3000

---

## 🐳 Running with Docker

If you prefer Docker, you can run the entire stack with one command:

```powershell
# Make sure .env is configured first
# Start both services
docker compose up --build

# Run in background (detached)
docker compose up --build -d

# Stop all services
docker compose down
```

| Service    | URL                           |
|------------|-------------------------------|
| Backend    | http://localhost:8000          |
| Frontend   | http://localhost:3000          |
| API Docs   | http://localhost:8000/docs     |

> `.env` is optional for booting the API, but live data collection requires the relevant API key credentials.

---

## 📊 Data Ingestion

Ingest data from external providers into MongoDB:

```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Ingest market data (XAUUSD candles from Twelve Data)
python scripts\ingest_all_markets.py

# Ingest financial news (from Marketaux)
python scripts\ingest_news.py

# Ingest economic data (from FRED/BLS/BEA)
python scripts\ingest_economic.py

# Backfill historical XAUUSD data
python scripts\backfill_xauusd.py
```

**Automatic ingestion:** Set `MARKET_INGESTION_ENABLED=TRUE` in `.env` to enable the background worker that auto-ingests candles every hour (configurable via `MARKET_INGESTION_INTERVAL_SECONDS`).

---

## 🤖 Model Training

Train the ML model to generate XAUUSD predictions:

```powershell
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1

# Step 1: Build features from raw data
python scripts\build_xauusd_features.py

# Step 2: Train the XAUUSD model
python scripts\train_xauusd.py

# Step 3 (optional): Run training pipeline step 3
python scripts\run_step3.py

# Weekly retraining with walk-forward validation
python scripts\train_weekly.py
```

Trained model artifacts are saved to `models/xauusd/`:
- `logistic_regression_final.joblib` — Trained model
- `feature_schema.json` — Feature definitions
- `final_metrics.json` — Performance metrics
- `calibration.json` — Probability calibration data
- `walk_forward_metrics.json` — Walk-forward validation results

> **Note:** The API serves predictions only when a trained model artifact exists. If no model has been trained, the API returns `MODEL_NOT_READY` (HTTP 503).

---

## 🧪 Testing

```powershell
# Backend unit tests
cd backend
..\.venv\Scripts\python.exe -m pytest -q

# Frontend build check
cd frontend
npm run build

# Verify configuration
cd ..
.\.venv\Scripts\python.exe scripts\verify_config.py
```

---

## 📡 API Reference

All endpoints are prefixed with `/api`.

| Method | Endpoint                      | Description                          |
|--------|-------------------------------|--------------------------------------|
| `GET`  | `/api/health`                 | Health check + DB & worker status    |
| `GET`  | `/api/market`                 | All market data summaries            |
| `GET`  | `/api/market/{symbol}`        | Market data for a specific symbol    |
| `GET`  | `/api/news`                   | Latest financial news                |
| `GET`  | `/api/economic-events`        | Economic events calendar             |
| `GET`  | `/api/predictions`            | All active predictions               |
| `GET`  | `/api/predictions/{symbol}`   | Prediction for a specific symbol     |
| `GET`  | `/api/model-performance`      | Model performance & metrics          |
| `GET`  | `/api/data-quality`           | Data quality report                  |
| `GET`  | `/api/explanations/{symbol}`  | SHAP-based feature explanations      |
| `GET`  | `/api/live-market`            | Live market data (WebSocket)         |
| `GET`  | `/api/war-room/{eventId}`     | War room analysis for an event       |

> **Error handling:** Missing data or untrained models return HTTP 503 with a clear message. Values are never invented.

Full interactive documentation available at: **http://localhost:8000/docs**

---

## 📁 Project Structure

```
AI_XAUUSD/
├── backend/                        # FastAPI Python backend
│   ├── app/
│   │   ├── api/                    #   REST API routes & middleware
│   │   │   └── routes/             #     health, market, news, predictions...
│   │   ├── collectors/             #   External data collectors
│   │   ├── core/                   #   Settings, logging configuration
│   │   ├── db/                     #   MongoDB client manager
│   │   ├── features/               #   Feature engineering pipeline
│   │   ├── ml/                     #   ML training & inference
│   │   ├── models/                 #   Pydantic data models
│   │   ├── providers/              #   External API provider adapters
│   │   ├── schemas/                #   Response schemas
│   │   ├── services/               #   Business logic services
│   │   └── main.py                 #   FastAPI app entry point
│   ├── requirements.txt            #   Python dependencies
│   └── Dockerfile                  #   Backend Docker config
│
├── frontend/                       # Next.js React frontend
│   ├── app/                        #   App Router pages
│   │   ├── page.js                 #     Main dashboard
│   │   ├── dashboard/              #     Dashboard page
│   │   └── war-room/               #     War room analysis
│   ├── components/                 #   React components
│   │   ├── PriceChart.js           #     Interactive price chart
│   │   ├── PredictionCard.js       #     Prediction display
│   │   ├── MarketCard.js           #     Market data card
│   │   ├── TechnicalPanel.js       #     Technical analysis panel
│   │   └── ...                     #     22 components total
│   ├── locales/                    #   i18n translations (EN, FR, AR)
│   ├── services/                   #   Centralized API client
│   ├── styles/                     #   Global CSS styles
│   └── package.json                #   Node.js dependencies
│
├── scripts/                        # Utility & ingestion scripts
│   ├── ingest_all_markets.py       #   Market data ingestion
│   ├── ingest_news.py              #   News ingestion
│   ├── ingest_economic.py          #   Economic data ingestion
│   ├── backfill_xauusd.py          #   Historical data backfill
│   ├── train_xauusd.py             #   Model training pipeline
│   ├── train_weekly.py             #   Weekly retraining
│   └── verify_config.py            #   Environment validation
│
├── models/                         # Trained ML model artifacts
│   └── xauusd/                     #   XAUUSD model files
│
├── data/                           # Data directory
│   ├── raw/                        #   Raw data files
│   ├── processed/                  #   Processed features
│   └── models/                     #   Runtime model path
│
├── tests/                          # Test suites
├── .env.example                    # Environment template
├── docker-compose.yml              # Docker multi-service config
├── PROJECT_ARCHITECTURE.md         # Architecture documentation
├── DEPLOYMENT.md                   # Deployment guide
└── README.md                       # ← You are here
```

---

## 🚀 Deployment

### Backend → Railway

1. Create a new project in Railway and link your GitHub repository
2. Set the root directory to `/backend`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables: `MONGODB_URI`, `DATABASE_NAME`, `ENVIRONMENT=production`, `API_CORS_ORIGINS=https://your-frontend.vercel.app`
5. Deploy and copy the HTTPS URL

### Frontend → Vercel

1. Import your GitHub repository to Vercel
2. Set root directory to `frontend`
3. Framework preset: **Next.js**
4. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app`
5. Deploy

### MongoDB Atlas

1. Create a free cluster (M0)
2. Create a least-privilege database user
3. Configure Network Access (allow deployment IPs)
4. Copy the connection string to `MONGODB_URI`

> See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full deployment guide.

---

## 🔧 Troubleshooting

| Problem                          | Solution                                                              |
|----------------------------------|-----------------------------------------------------------------------|
| `ModuleNotFoundError`            | Activate venv: `.\.venv\Scripts\Activate.ps1` then `pip install -r backend\requirements.txt` |
| Backend won't start              | Check `.env` exists and `MONGODB_URI` is valid                        |
| Frontend shows "Loading..."      | Verify backend is running at `http://localhost:8000/api/health`       |
| CORS errors in browser           | Check `API_CORS_ORIGINS` in `.env` includes `http://localhost:3000`   |
| `MODEL_NOT_READY` (503)          | Run `python scripts\train_xauusd.py` to train the model first        |
| MongoDB connection timeout       | Check your Atlas Network Access allows your IP address                |
| Port already in use              | Kill existing process: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F` |
| `npm install` fails              | Delete `node_modules` and `package-lock.json`, then retry             |
| Docker build fails               | Ensure Docker Desktop is running and `.env` exists                    |

---

## 📄 Rapport PFA (FR)

Le rapport technique en français, basé sur l'architecture actuelle du dépôt, est disponible dans:
- [`README_RAPPORT_PFA.md`](README_RAPPORT_PFA.md) — Rapport complet
- [`README_API.md`](README_API.md) — Documentation de l'API

---

## 📜 License

This project is for **research and educational purposes only**. It does not constitute financial advice.

---

<p align="center">
  <b>Built with ❤️ for quantitative research</b><br>
  <sub>Python 3.13 • FastAPI • Next.js 15 • MongoDB Atlas • scikit-learn • XGBoost</sub>
</p>

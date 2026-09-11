# AI Market Intelligence

Portable financial-market research dashboard. It does not trade automatically or promise returns.

## Setup
1. Copy `.env.example` to `.env` and set MongoDB Atlas and provider secrets locally.
2. Install backend dependencies: `.venv\Scripts\python -m pip install -r backend\requirements.txt`.
3. Run API from `backend`: `..\.venv\Scripts\python -m uvicorn app.main:app --reload`.
4. Run frontend from `frontend`: `npm install; npm run dev`.

## Docker
Start Docker Desktop, then run `docker compose up --build`.

## Deployment
Deploy `frontend` to Vercel, `backend` to Railway, and configure MongoDB Atlas via environment variables. Never commit `.env`.
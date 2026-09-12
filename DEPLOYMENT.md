# Deployment Guide

## Architecture
The platform consists of a FastAPI backend (Python) and a Next.js frontend (React), connected to a MongoDB Atlas database.

## Prerequisites
- MongoDB Atlas cluster
- Vercel account (for frontend)
- Railway or Render account (for backend)
- API Keys: Twelve Data (Market Data), News APIs, Economic APIs

## Backend Deployment (Railway)
1. Create a new project in Railway and link your GitHub repository.
2. Select the `/backend` folder as the root.
3. Railway should automatically detect `requirements.txt` and install dependencies.
4. Set the Start Command to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `ENVIRONMENT=production`
   - `MONGODB_URI`
   - `DATABASE_NAME`
   - `MARKET_DATA_API_KEY`
   - `API_CORS_ORIGINS=https://your-frontend-domain.vercel.app`
6. Deploy and copy the provided HTTPS URL.

## Frontend Deployment (Vercel)
1. Import your GitHub repository to Vercel.
2. Set the Root Directory to `frontend`.
3. The framework preset should be Next.js.
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend-domain.up.railway.app`
5. Click Deploy.

## MongoDB Atlas Setup
1. Create a free cluster.
2. Under Database Access, create a user with least-privilege access (read/write to specific DB).
3. Under Network Access, allow IPs (either `0.0.0.0/0` for cloud deployments or specific IPs).
4. Copy the connection string to your `MONGODB_URI` environment variable.

## Docker (Local/Self-hosted)
If you prefer to self-host using Docker:
```bash
docker compose build
docker compose up -d
```
Make sure your `.env` file is populated.


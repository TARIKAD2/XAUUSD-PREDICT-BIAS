import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.client import MongoClientManager
from app.core.config import get_settings

@pytest.mark.asyncio
async def test_apis():
    settings = get_settings()
    manager = MongoClientManager(settings)
    await manager.connect()
    
    # We must replace the app's manager so it uses our connected one
    app.state.mongo_manager = manager
    
    with TestClient(app) as client:
        try:
            r1 = client.get("/api/predictions/XAUUSD")
            print("=== GET /api/predictions/XAUUSD ===")
            print(f"Status: {r1.status_code}")
            print(r1.json())
            
            r2 = client.get("/api/model-performance")
            print("\n=== GET /api/model-performance ===")
            print(f"Status: {r2.status_code}")
            print(r2.json())
        finally:
            await manager.disconnect()

if __name__ == "__main__":
    asyncio.run(test_apis())

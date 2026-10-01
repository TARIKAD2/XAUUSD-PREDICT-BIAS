import asyncio
from datetime import timedelta
import json
from datetime import datetime, timezone
from unittest import mock

import pytest
import pytest_asyncio
from app.services.live_market import live_market_service

# Helper fake websocket
class FakeWebSocket:
    def __init__(self, messages):
        self._messages = asyncio.Queue()
        for msg in messages:
            self._messages.put_nowait(msg)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def send(self, data: str):
        self.sent.append(data)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await self._messages.get()
        except asyncio.CancelledError:
            raise StopAsyncIteration

    async def close(self):
        pass

@pytest_asyncio.fixture(autouse=True)
async def cleanup_service():
    # Ensure service is stopped before each test
    await live_market_service.stop()
    yield
    await live_market_service.stop()

@pytest.mark.asyncio
async def test_price_parsing_and_status_update():
    # Prepare a single price message for XAU/USD
    price_msg = json.dumps({
        "type": "price",
        "symbol": "XAU/USD",
        "price": "4300.123",
        "timestamp": "2023-01-01T00:00:00Z",
    })

    fake_ws = FakeWebSocket([price_msg])
    with mock.patch('app.services.live_market.websockets.connect', return_value=fake_ws):
        await live_market_service.start()
        # Give some time for the receive loop to process the message
        await asyncio.sleep(0.1)
        status = live_market_service.get_status()
        assert status["provider_state"] == "CONNECTED"
        sym_info = status["symbols"]["XAU/USD"]
        assert sym_info["status"] in {"LIVE", "DELAYED", "STALE"}
        assert sym_info["latest_tick"]["price"] == "4300.123"

@pytest.mark.asyncio
async def test_subscriber_queue_receives_tick():
    price_msg = json.dumps({
        "type": "price",
        "symbol": "XAU/USD",
        "price": "4300.123",
        "timestamp": "2023-01-01T00:00:01Z",
    })
    fake_ws = FakeWebSocket([price_msg])
    with mock.patch('app.services.live_market.websockets.connect', return_value=fake_ws):
        await live_market_service.start()
        q = await live_market_service.add_subscriber()
        # Wait for the message to be broadcast
        tick = await asyncio.wait_for(q.get(), timeout=1.0)
        assert tick["symbol"] == "XAU/USD"
        assert tick["price"] == "4300.123"
        await live_market_service.remove_subscriber(q)

@pytest.mark.asyncio
async def test_unavailable_symbol_handling():
    sub_status_msg = json.dumps({
        "type": "subscription_status",
        "symbol": "XAU/USD",
        "status": "error",
        "message": "Symbol not supported"
    })
    fake_ws = FakeWebSocket([sub_status_msg])
    with mock.patch('app.services.live_market.websockets.connect', return_value=fake_ws):
        await live_market_service.start()
        await asyncio.sleep(0.1)
        status = live_market_service.get_status()
        assert status["symbols"]["XAU/USD"]["status"] == "UNAVAILABLE"

@pytest.mark.asyncio
async def test_freshness_thresholds():
    # Two messages: one recent, one stale (old timestamp)
    recent_msg = json.dumps({
        "type": "price",
        "symbol": "XAU/USD",
        "price": "4300.50",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    stale_time = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    stale_msg = json.dumps({
        "type": "price",
        "symbol": "XAU/USD",
        "price": "4300.10",
        "timestamp": stale_time
    })
    fake_ws = FakeWebSocket([stale_msg, recent_msg])
    with mock.patch('app.services.live_market.websockets.connect', return_value=fake_ws):
        await live_market_service.start()
        await asyncio.sleep(0.2)
        status = live_market_service.get_status()
        # With default freshness (5s live, 30s delayed) the recent tick makes it LIVE
        assert status["symbols"]["XAU/USD"]["status"] == "LIVE"

# FastAPI endpoint tests
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_live_status_endpoint():
    # Mock provider state to CONNECTED and a known tick
    live_market_service._provider_state = "CONNECTED"
    live_market_service._latest_ticks = {
        "XAU/USD": {"symbol": "XAU/USD", "price": "4300", "received_at": datetime.now(timezone.utc).isoformat()}
    }
    live_market_service._symbol_status = {"XAU/USD": "LIVE"}
    resp = client.get("/api/market/live-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider_state"] == "CONNECTED"
    assert data["symbols"]["XAU/USD"]["status"] == "LIVE"

def test_websocket_endpoint():
    with client.websocket_connect("/ws/market") as websocket:
        # Simulate a tick via service broadcast
        tick = {"symbol": "XAU/USD", "price": "4300", "timestamp": "2023-01-01T00:00:00Z"}
        # Directly broadcast using the internal method
        import asyncio
        asyncio.run(live_market_service._broadcast_tick(tick))
        received = websocket.receive_json()
        assert received["symbol"] == "XAU/USD"
        assert received["price"] == "4300"

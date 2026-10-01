from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from app.services.live_market import live_market_service

router = APIRouter()

@router.get("/market/live-status")
async def live_status() -> Dict[str, Any]:
    """Return provider connection state and per‑symbol live status."""
    return live_market_service.get_status()

@router.websocket("/ws/market")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    queue = await live_market_service.add_subscriber()
    try:
        while True:
            tick = await queue.get()
            await ws.send_json(tick)
    except WebSocketDisconnect:
        await live_market_service.remove_subscriber(queue)
    except Exception:
        await live_market_service.remove_subscriber(queue)
        raise

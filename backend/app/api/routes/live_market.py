import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from app.services.live_market import live_market_service

router = APIRouter()

@router.get("/market/live-status")
async def live_status(response: Response) -> Dict[str, Any]:
    """Return provider connection state and per‑symbol live status."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return live_market_service.get_status()

@router.websocket("/ws/market")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    queue = await live_market_service.add_subscriber()
    try:
        while True:
            try:
                tick = await asyncio.wait_for(queue.get(), timeout=10.0)
                await ws.send_json(tick)
            except asyncio.TimeoutError:
                # Keepalive heartbeat frame to prevent browser/proxy idle drop
                await ws.send_json({
                    "type": "heartbeat",
                    "event": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        await live_market_service.remove_subscriber(queue)
    except Exception:
        await live_market_service.remove_subscriber(queue)
        raise


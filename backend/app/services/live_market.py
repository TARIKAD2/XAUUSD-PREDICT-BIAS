import asyncio
import inspect
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Set

import websockets
from websockets import WebSocketClientProtocol

from app.core.config import get_settings
from app.core.logging import get_logger

# ---------------------------------------------------------------------------
# Enums for symbol and provider state
# ---------------------------------------------------------------------------
class SymbolStatus(str, Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    WAITING_FOR_TICK = "WAITING_FOR_TICK"
    UNAVAILABLE = "UNAVAILABLE"
    OFFLINE = "OFFLINE"

class ProviderState(str, Enum):
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    DISCONNECTED = "DISCONNECTED"

# ---------------------------------------------------------------------------
# Service implementation
# ---------------------------------------------------------------------------
class LiveMarketService:
    """Singleton service that maintains a resilient Twelve Data WebSocket connection
    and distributes real-time price ticks to FastAPI WebSocket subscribers.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._lock: asyncio.Lock | None = None
        self._settings = get_settings()
        self._logger = get_logger(__name__)
        self._provider_state: ProviderState = ProviderState.DISCONNECTED
        self._ws: Any = None
        self._supervisor_task: asyncio.Task | None = None
        self._receive_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._subscriber_queues: Set[asyncio.Queue] = set()
        self._latest_ticks: Dict[str, Dict[str, Any]] = {}
        self._symbol_status: Dict[str, SymbolStatus] = {}
        self._stopped = False
        self._supported_symbols = [
            "XAU/USD",
        ]
        for sym in self._supported_symbols:
            self._symbol_status[sym] = SymbolStatus.WAITING_FOR_TICK

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ---------------------------------------------------------------------
    # Public lifecycle methods used by FastAPI
    # ---------------------------------------------------------------------
    async def start(self) -> None:
        async with self._get_lock():
            if self._supervisor_task and not self._supervisor_task.done():
                return
            self._stopped = False
            self._provider_state = ProviderState.CONNECTING
            self._logger.info("live_market:start", extra={"state": "CONNECTING"})
            self._supervisor_task = asyncio.create_task(self._supervisor_loop())

    async def stop(self) -> None:
        self._stopped = True
        if self._supervisor_task:
            self._supervisor_task.cancel()
            try:
                await self._supervisor_task
            except (asyncio.CancelledError, Exception):
                pass
            self._supervisor_task = None

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except (asyncio.CancelledError, Exception):
                pass
            self._reconnect_task = None

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except (asyncio.CancelledError, Exception):
                pass
            self._receive_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        self._provider_state = ProviderState.DISCONNECTED
        self._logger.info("live_market:stop", extra={"state": "DISCONNECTED"})

        # Reset state for next lifecycle
        self._lock = None
        self._subscriber_queues.clear()
        self._latest_ticks.clear()
        for sym in self._supported_symbols:
            self._symbol_status[sym] = SymbolStatus.WAITING_FOR_TICK

    # ---------------------------------------------------------------------
    # Subscriber management (FastAPI WebSocket handlers)
    # ---------------------------------------------------------------------
    async def add_subscriber(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._get_lock():
            self._subscriber_queues.add(q)
            # Push cached latest ticks to the new subscriber immediately
            for tick in self._latest_ticks.values():
                initial_tick = tick.copy()
                initial_tick["type"] = "initial_state"
                initial_tick["event"] = "initial_state"
                try:
                    if q.full():
                        _ = q.get_nowait()
                    q.put_nowait(initial_tick)
                except Exception:
                    pass
        return q

    async def remove_subscriber(self, q: asyncio.Queue) -> None:
        async with self._get_lock():
            self._subscriber_queues.discard(q)

    # ---------------------------------------------------------------------
    # Status endpoint data
    # ---------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        provider_state = (
            self._provider_state.value
            if isinstance(self._provider_state, ProviderState)
            else str(self._provider_state)
        )
        result: Dict[str, Any] = {
            "provider_state": provider_state,
            "symbols": {},
        }
        for sym in self._supported_symbols:
            raw_tick = self._latest_ticks.get(sym)
            raw_status = self._symbol_status.get(sym, SymbolStatus.OFFLINE)
            if isinstance(raw_status, SymbolStatus):
                status = raw_status
            else:
                try:
                    status = SymbolStatus(raw_status)
                except Exception:
                    status = SymbolStatus(str(raw_status))

            tick = None
            if raw_tick:
                received_at = raw_tick.get("received_at")
                if isinstance(received_at, str):
                    try:
                        received_at_dt = datetime.fromisoformat(received_at)
                    except Exception:
                        received_at_dt = now
                elif isinstance(received_at, datetime):
                    received_at_dt = received_at
                else:
                    received_at_dt = now

                age = (now - received_at_dt).total_seconds()
                if age <= self._settings.live_freshness_live_sec:
                    status = SymbolStatus.LIVE
                elif age <= self._settings.live_freshness_delayed_sec:
                    status = SymbolStatus.DELAYED
                else:
                    status = SymbolStatus.STALE

                tick = {k: v for k, v in raw_tick.items() if k != "received_at"}
                tick["received_at"] = received_at_dt.isoformat()

            if provider_state == ProviderState.DISCONNECTED.value and status != SymbolStatus.UNAVAILABLE:
                status = SymbolStatus.OFFLINE

            result["symbols"][sym] = {
                "status": status.value,
                "latest_tick": tick,
            }
        return result

    # ---------------------------------------------------------------------
    # Supervisor connection and message loop
    # ---------------------------------------------------------------------
    async def _supervisor_loop(self) -> None:
        attempt = 0
        while not self._stopped:
            try:
                self._provider_state = ProviderState.CONNECTING
                # Mask API key in all logging
                self._logger.info("live_market:connecting", extra={"url": "wss://ws.twelvedata.com/v1/quotes/price?apikey=***"})

                api_key = self._settings.twelve_data_api_key.get_secret_value()
                ws_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={api_key}"

                try:
                    connect_call = websockets.connect(
                        ws_url,
                        ping_interval=20,
                        ping_timeout=20,
                        close_timeout=10,
                    )
                except TypeError:
                    # Support mock objects that don't accept ping kwargs
                    connect_call = websockets.connect(ws_url)

                if inspect.isawaitable(connect_call):
                    ws = await connect_call
                else:
                    ws = connect_call

                self._ws = ws
                symbols_param = ",".join(self._supported_symbols)
                sub_msg = json.dumps({"action": "subscribe", "params": {"symbols": symbols_param}})
                await self._ws.send(sub_msg)
                self._provider_state = ProviderState.CONNECTED
                self._logger.info("live_market:connected", extra={"symbols": symbols_param})
                attempt = 0  # reset reconnect delay on successful connection

                for sym in self._supported_symbols:
                    if self._symbol_status.get(sym) != SymbolStatus.UNAVAILABLE:
                        self._symbol_status[sym] = SymbolStatus.WAITING_FOR_TICK

                # Iterate incoming messages from Twelve Data
                async for raw_msg in self._ws:
                    if self._stopped:
                        break
                    await self._process_message(raw_msg)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self._provider_state = ProviderState.DISCONNECTED
                self._logger.warning(
                    "live_market:connection_error",
                    extra={"error": str(exc), "attempt": attempt},
                )
            else:
                self._provider_state = ProviderState.DISCONNECTED
                self._logger.info("live_market:connection_closed")
            finally:
                if self._ws:
                    try:
                        await self._ws.close()
                    except Exception:
                        pass
                    self._ws = None

            if not self._stopped:
                base = self._settings.live_reconnect_base_seconds
                max_sec = self._settings.live_reconnect_max_seconds
                delay = min(base * (2 ** attempt), max_sec)
                attempt += 1
                self._logger.info("live_market:reconnecting", extra={"delay_sec": delay, "attempt": attempt})
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    break

    async def _process_message(self, raw_msg: str) -> None:
        try:
            msg = json.loads(raw_msg)
        except Exception:
            self._logger.debug("live_market:non_json_message", extra={"msg": str(raw_msg)})
            return

        self._logger.debug("live_market:message", extra={"msg": msg})

        # Heartbeat
        if msg.get("type") == "heartbeat" or msg.get("event") == "heartbeat":
            return

        # Subscription status
        event_name = msg.get("event") or msg.get("type")
        if event_name in ("subscribe-status", "subscription_status"):
            sym = msg.get("symbol") or msg.get("symbol_name")
            if sym and sym.upper() in self._supported_symbols:
                if msg.get("status") == "error":
                    self._symbol_status[sym.upper()] = SymbolStatus.UNAVAILABLE
                    self._logger.warning(
                        "live_market:symbol_unavailable",
                        extra={"symbol": sym, "message": msg.get("message")},
                    )
            return

        # Price event (Twelve Data uses event: "price" and type: "Precious Metal" or similar)
        if msg.get("event") == "price" or msg.get("type") == "price":
            sym = msg.get("symbol") or msg.get("symbol_name")
            if not sym:
                return
            sym = sym.upper()
            if sym not in self._supported_symbols:
                return

            now = datetime.now(timezone.utc)
            provider_ts = msg.get("timestamp") or msg.get("datetime")
            provider_iso = None
            latency_ms = None

            if provider_ts is not None:
                try:
                    if isinstance(provider_ts, (int, float)):
                        ts_sec = provider_ts / 1000.0 if provider_ts > 1e11 else float(provider_ts)
                        prov_dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
                        provider_iso = prov_dt.isoformat()
                        latency_ms = max(0, int((now - prov_dt).total_seconds() * 1000))
                    elif isinstance(provider_ts, str):
                        if provider_ts.isdigit():
                            val = float(provider_ts)
                            ts_sec = val / 1000.0 if val > 1e11 else val
                            prov_dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
                            provider_iso = prov_dt.isoformat()
                            latency_ms = max(0, int((now - prov_dt).total_seconds() * 1000))
                        else:
                            prov_dt = datetime.fromisoformat(provider_ts.rstrip("Z")).replace(tzinfo=timezone.utc)
                            provider_iso = prov_dt.isoformat()
                            latency_ms = max(0, int((now - prov_dt).total_seconds() * 1000))
                except Exception:
                    provider_iso = str(provider_ts)

            raw_price = msg.get("price") if "price" in msg and msg.get("price") is not None else msg.get("value")

            tick: Dict[str, Any] = {
                "type": "price",
                "event": "price",
                "symbol": sym,
                "normalized_symbol": sym.replace("/", ""),
                "price": raw_price,
                "provider_timestamp": provider_ts,
                "provider_time": provider_iso,
                "iso_timestamp": provider_iso or str(provider_ts),
                "received_at": now.isoformat(),
                "latency_ms": latency_ms,
            }

            self._latest_ticks[sym] = tick
            self._symbol_status[sym] = SymbolStatus.LIVE
            await self._broadcast_tick(tick)

    async def _broadcast_tick(self, tick: Dict[str, Any]) -> None:
        dead: List[asyncio.Queue] = []
        for q in list(self._subscriber_queues):
            if q.full():
                try:
                    _ = q.get_nowait()
                except Exception:
                    pass
            try:
                q.put_nowait(tick)
            except Exception:
                dead.append(q)
        for d in dead:
            self._subscriber_queues.discard(d)

# Export a shared singleton for import convenience
live_market_service = LiveMarketService()

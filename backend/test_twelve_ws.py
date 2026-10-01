import asyncio
import json
from app.core.config import get_settings

# Constants
WEBSOCKET_ENDPOINT = "wss://ws.twelvedata.com/v1/quotes/price"
SUBSCRIBE_MESSAGE = json.dumps({
    "action": "subscribe",
    "params": {"symbols": "XAU/USD"}
})
HEARTBEAT_MESSAGE = json.dumps({"action": "heartbeat"})

async def heartbeat_loop(ws):
    """Send a heartbeat every ~10 seconds to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(10)
            await ws.send(HEARTBEAT_MESSAGE)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print("Heartbeat error:", e)

async def main():
    # Load settings (API key is kept secret)
    settings = get_settings()
    api_key = settings.twelve_data_api_key.get_secret_value()

    ws_url = f"{WEBSOCKET_ENDPOINT}?apikey={api_key}"

    print("========================================")
    print("TWELVE DATA LIVE WEBSOCKET TEST")
    print("========================================\n")
    print("Provider: Twelve Data")
    print("Symbol: XAU/USD\n")
    print("Endpoint:")
    print(WEBSOCKET_ENDPOINT + "?apikey=*****")

    try:
        import websockets
    except Exception as e:
        print("WebSocket library missing:", e)
        return

    try:
        async with websockets.connect(ws_url) as ws:
            print("WebSocket: CONNECTED")

            # 1. Subscribe
            await ws.send(SUBSCRIBE_MESSAGE)
            try:
                sub_resp = await asyncio.wait_for(ws.recv(), timeout=10)
                print("Subscription response:")
                print(sub_resp)
            except asyncio.TimeoutError:
                print("Subscription: FAIL (no response)")
                print("\nLIVE STREAM: FAIL")
                return
            else:
                print("Subscription: PASS")

            # Start heartbeat in background
            hb_task = asyncio.create_task(heartbeat_loop(ws))

            price_events = []
            start_time = asyncio.get_event_loop().time()
            # Collect messages for up to 30 seconds or until we have at least 2 price events
            while len(price_events) < 2 and (asyncio.get_event_loop().time() - start_time) < 30:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10)
                except asyncio.TimeoutError:
                    break
                try:
                    data = json.loads(msg)
                except Exception:
                    # Non‑JSON message, just continue
                    continue
                # Look for price events
                if data.get("type") == "price" or data.get("event") == "price" or data.get("type") == "trade":
                    price_events.append(data)

            hb_task.cancel()
            # Reporting
            print("\nMessages received:", len(price_events))
            if price_events:
                first = price_events[0]
                latest = price_events[-1]
                print("Actual price events: YES")
                print("\nFirst tick:")
                print("Symbol:", first.get("symbol") or first.get("symbol_name") or "XAU/USD")
                print("Price:", first.get("price") or first.get("value"))
                print("Timestamp:", first.get("timestamp") or first.get("datetime"))
                print("Exchange:", first.get("exchange") or "N/A")
                print("\nLatest tick:")
                print("Symbol:", latest.get("symbol") or latest.get("symbol_name") or "XAU/USD")
                print("Price:", latest.get("price") or latest.get("value"))
                print("Timestamp:", latest.get("timestamp") or latest.get("datetime"))
                print("Exchange:", latest.get("exchange") or "N/A")
                print("\nLIVE STREAM: PASS")
            else:
                print("Actual price events: NO")
                print("\nLIVE STREAM: FAIL")
    except Exception as e:
        # Connection or protocol error
        if hasattr(e, "status_code") and e.status_code == 404:
            print("WebSocket: FAIL")
            print("Error: HTTP 404")
        else:
            print("WebSocket: FAIL")
            print("Error:", e)
        print("\nLIVE STREAM: FAIL")

if __name__ == "__main__":
    asyncio.run(main())

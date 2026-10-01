"""
60-second real Twelve Data & FastAPI WebSocket verification test.
Connects to ws://localhost:8000/ws/market, streams real ticks for 60 seconds,
and records tick count, timestamps, prices, and latencies.
"""
import asyncio
import json
import time
import websockets

FASTAPI_WS_URL = "ws://localhost:8000/ws/market"
TEST_DURATION = 60

async def main():
    print(f"[VERIFY] Connecting to {FASTAPI_WS_URL}...")
    ticks = []
    start_time = time.time()
    deadline = start_time + TEST_DURATION

    async with websockets.connect(FASTAPI_WS_URL) as ws:
        print("[VERIFY] Connected to FastAPI WebSocket!")
        while time.time() < deadline:
            remaining = deadline - time.time()
            try:
                raw_msg = await asyncio.wait_for(ws.recv(), timeout=min(5.0, max(0.1, remaining)))
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                print("[VERIFY] WebSocket closed by server")
                break

            try:
                data = json.loads(raw_msg)
            except Exception:
                continue

            event_type = data.get("type") or data.get("event")
            symbol = data.get("symbol") or data.get("normalized_symbol")
            price = data.get("price")
            ts = data.get("provider_time") or data.get("provider_timestamp")
            received_at = data.get("received_at")
            latency = data.get("latency_ms")

            elapsed = time.time() - start_time
            tick_record = {
                "index": len(ticks) + 1,
                "elapsed_sec": round(elapsed, 2),
                "type": event_type,
                "symbol": symbol,
                "price": price,
                "provider_time": ts,
                "received_at": received_at,
                "latency_ms": latency
            }
            ticks.append(tick_record)
            print(f"[{elapsed:5.1f}s] Tick #{len(ticks)}: {symbol} = {price} | prov_ts: {ts} | rec_at: {received_at} | lat: {latency}ms")

    total_elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"[VERIFICATION SUMMARY]")
    print(f"Total time: {total_elapsed:.1f}s")
    print(f"Total ticks received: {len(ticks)}")

    price_ticks = [t for t in ticks if t["price"] is not None]
    unique_prices = set(t["price"] for t in price_ticks)
    print(f"Total price ticks: {len(price_ticks)}")
    print(f"Unique price values: {len(unique_prices)}")

    if ticks:
        print(f"First tick: #{ticks[0]['index']} @ {ticks[0]['elapsed_sec']}s -> price={ticks[0]['price']} ({ticks[0]['provider_time']})")
        print(f"Last tick:  #{ticks[-1]['index']} @ {ticks[-1]['elapsed_sec']}s -> price={ticks[-1]['price']} ({ticks[-1]['provider_time']})")

    print("=" * 80)

    # Save results to json for report
    with open("scratch/60s_verification_results.json", "w") as f:
        json.dump({
            "total_elapsed": total_elapsed,
            "tick_count": len(ticks),
            "price_tick_count": len(price_ticks),
            "unique_prices_count": len(unique_prices),
            "first_tick": ticks[0] if ticks else None,
            "last_tick": ticks[-1] if ticks else None,
            "sample_ticks": ticks[:25]
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())

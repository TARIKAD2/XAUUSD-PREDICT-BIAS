import asyncio
import httpx
from app.core.config import get_settings
from app.db.client import MongoClientManager

async def test_twelve_data(api_key):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1h&apikey={api_key}&outputsize=1")
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "error":
                return "FAIL", data.get("message")
            return "PASS", r.status_code
        return "FAIL", f"HTTP {r.status_code}"

async def test_marketaux(api_key):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.marketaux.com/v1/news/all?symbols=XAUUSD&api_token={api_key}&limit=1")
        if r.status_code == 200:
            return "PASS", r.status_code
        elif r.status_code == 401:
            return "FAIL", "Unauthorized"
        return "FAIL", f"HTTP {r.status_code}: {r.text[:50]}"

async def test_fred(api_key):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.stlouisfed.org/fred/series?series_id=GNPCA&api_key={api_key}&file_type=json")
        if r.status_code == 200:
            return "PASS", r.status_code
        return "FAIL", f"HTTP {r.status_code}: {r.text[:50]}"

async def test_bea(api_key):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://apps.bea.gov/api/data/?&UserID={api_key}&method=GETDATASETLIST&ResultFormat=JSON")
        if r.status_code == 200:
            data = r.json()
            if "BEAAPI" in data and "Error" in data["BEAAPI"]:
                return "FAIL", data["BEAAPI"]["Error"]["ErrorDetail"]["Description"]
            return "PASS", r.status_code
        return "FAIL", f"HTTP {r.status_code}"

async def test_eodhd(api_key):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://eodhd.com/api/real-time/AAPL.US?api_token={api_key}&fmt=json")
        if r.status_code == 200:
            return "PASS", r.status_code
        return "FAIL", f"HTTP {r.status_code}"

async def test_bls(api_key):
    # BLS needs POST for proper validation or just GET a simple series
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", json={"seriesid": ["CUUR0000SA0"], "registrationkey": api_key})
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "REQUEST_NOT_PROCESSED":
                return "FAIL", data.get("message")
            return "PASS", r.status_code
        return "FAIL", f"HTTP {r.status_code}"

async def main():
    settings = get_settings()
    print(f".env loading: PASS")
    
    manager = MongoClientManager(settings)
    connected = await manager.connect()
    print(f"MongoDB connection: {'PASS' if connected else 'FAIL'}")
    await manager.disconnect()

    providers = {
        "Twelve Data": ("twelve_data_api_key", test_twelve_data),
        "MarketAux": ("marketaux_api_key", test_marketaux),
        "FRED": ("fred_api_key", test_fred),
        "BEA": ("bea_api_key", test_bea),
        "EODHD": ("eodhd_api_key", test_eodhd),
        "BLS": ("bls_api_key", test_bls),
    }

    for name, (var_name, test_func) in providers.items():
        print(f"\nPROVIDER: {name}")
        print(f"- environment variable expected: {var_name.upper()}")
        secret = getattr(settings, var_name)
        if secret and secret.get_secret_value().strip():
            print(f"- credential detected: YES")
            try:
                status, msg = await test_func(secret.get_secret_value().strip())
                print(f"- connection/authentication test: {status}")
                if status == "PASS":
                    print(f"- HTTP/status result if safe to report: {msg}")
                else:
                    print(f"- error message if failed: {msg}")
                    print(f"- exact file/line causing the issue: configuration / missing valid key")
                    print(f"- recommended fix: Verify the API key in .env")
            except Exception as e:
                print(f"- connection/authentication test: FAIL")
                print(f"- error message if failed: {str(e)}")
        else:
            print(f"- credential detected: NO")
            print(f"- connection/authentication test: FAIL")
            print(f"- error message if failed: API key is missing or empty")
            print(f"- recommended fix: Add {var_name.upper()} to .env")

if __name__ == "__main__":
    asyncio.run(main())

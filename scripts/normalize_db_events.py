import asyncio
import sys

sys.path.insert(0, "backend")

from app.db.client import MongoClientManager
from app.core.config import get_settings
from app.db.collections import ECONOMIC_EVENTS

UNIT_MAP = {
    "US Consumer Price Index (CPI)": "Index",
    "US PCE Price Index": "Index",
    "US Unemployment Rate": "%",
    "US Nonfarm Payrolls (NFP)": "K",
    "US Initial Jobless Claims": "Claims",
    "Federal Funds Effective Rate": "%",
    "US Gross Domestic Product (GDP)": "B USD",
    "US Retail Sales": "M USD",
    "US Producer Price Index (PPI)": "Index",
    "US JOLTS Job Openings": "K",
    "ISM Manufacturing PMI": "Index",
    "US CPI (BLS)": "Index",
    "US Nonfarm Payrolls (BLS)": "K",
    "US Unemployment Rate (BLS)": "%",
    "US Labor Productivity": "%",
    "US GDP (BEA)": "B USD",
}

async def main():
    m = MongoClientManager(get_settings())
    if not await m.connect():
        print("Failed to connect.")
        return
    docs = await m.database[ECONOMIC_EVENTS].find({}).to_list(500)
    print("Total documents in collection:", len(docs))
    updated = 0
    for d in docs:
        ev_name = d.get("event")
        expected_unit = UNIT_MAP.get(ev_name)
        updates = {}
        if expected_unit and d.get("unit") != expected_unit:
            updates["unit"] = expected_unit
        if not d.get("provider"):
            prov = "FRED" if "BLS" not in ev_name and "BEA" not in ev_name else ("BLS" if "BLS" in ev_name else "BEA")
            updates["provider"] = prov
            updates["source"] = prov
        if updates:
            await m.database[ECONOMIC_EVENTS].update_one({"_id": d["_id"]}, {"$set": updates})
            updated += 1
    print(f"Normalized {updated} documents in MongoDB.")
    await m.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

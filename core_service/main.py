from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time
import os
import uvicorn
import sys

# Add shared directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.constants import (
    NEPSELYTICS_URL, 
    NEPSE_TURNOVER_URL, 
    NEPALIPAISA_INDEX_URL, 
    NEPALIPAISA_SUBINDEX_URL,
    DEFAULT_HEADERS
)

app = FastAPI(title="NEPSE Core Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "Core Service Running", "service": "Core/Live"}

@app.get("/homepage-data")
async def homepage_data():
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NEPSELYTICS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch homepage market data")
    return resp.json()

@app.get("/market-turnover")
async def market_turnover():
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NEPSE_TURNOVER_URL, headers=DEFAULT_HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch NEPSE market turnover")
    return resp.json()

@app.get("/index-live")
async def index_live():
    headers = {**DEFAULT_HEADERS, "Referer": "https://nepalipaisa.com"}
    params = {"_": int(time.time() * 1000)}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NEPALIPAISA_INDEX_URL, headers=headers, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch NEPSE index live data")
    return resp.json()

@app.get("/subindex-live")
async def subindex_live():
    headers = {**DEFAULT_HEADERS, "Referer": "https://nepalipaisa.com"}
    params = {"_": int(time.time() * 1000)}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NEPALIPAISA_SUBINDEX_URL, headers=headers, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch NEPSE sub-index live data")
    return resp.json()

@app.get("/floorsheet")
async def floorsheet(
    page: int = Query(0, ge=0),
    size: int = Query(500, ge=1, le=500),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    from shared.constants import NEPSELYTICS_FLOORSHEET_URL
    headers = {**DEFAULT_HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    if size > 100:
        all_records = []
        pages_needed = (size + 99) // 100
        async with httpx.AsyncClient(timeout=30) as client:
            for i in range(pages_needed):
                params = {"page": page + i, "Size": 100, "order": order}
                resp = await client.get(NEPSELYTICS_FLOORSHEET_URL, params=params, headers=headers)
                if resp.status_code != 200: break
                records = resp.json().get("data", {}).get("content", [])
                all_records.extend(records)
                if len(records) < 100: break
        return {"success": True, "data": all_records[:size]}
    else:
        params = {"page": page, "Size": size, "order": order}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(NEPSELYTICS_FLOORSHEET_URL, params=params, headers=headers)
        return resp.json()

@app.get("/floorsheet/totals")
async def floorsheet_totals():
    from shared.constants import NEPSELYTICS_FLOORSHEET_URL
    headers = DEFAULT_HEADERS
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NEPSELYTICS_FLOORSHEET_URL, params={"page": 0, "Size": 1, "order": "desc"}, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch floorsheet totals")
    data = resp.json().get("data", {})
    return {"success": True, "data": {"totalAmount": data.get("totalAmount", 0), "totalQty": data.get("totalQty", 0), "totalTrades": data.get("totalTrades", 0)}}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

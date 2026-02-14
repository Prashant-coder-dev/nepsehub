from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import uvicorn
import sys

# Add shared directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.constants import (
    SHAREHUB_ANNOUNCEMENT_URL, 
    SHAREHUB_OFFERING_URL,
    DEFAULT_HEADERS
)

app = FastAPI(title="NEPSE Market Info Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_offerings(type: int, for_category: int, size: int = 30):
    """Fetch offerings with both size=5 and size=30 and combine results"""
    all_data = []
    seen_ids = set()
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch with size=5
        params_5 = {"size": 5, "type": type, "for": for_category}
        try:
            resp = await client.get(SHAREHUB_OFFERING_URL, params=params_5, headers=DEFAULT_HEADERS)
            if resp.status_code == 200:
                page_data = resp.json()
                if isinstance(page_data, dict) and "data" in page_data:
                    items = page_data.get("data", [])
                    if isinstance(items, list):
                        for item in items:
                            # Use a unique identifier to avoid duplicates
                            item_id = item.get("id") or item.get("symbol") or str(item)
                            if item_id not in seen_ids:
                                seen_ids.add(item_id)
                                all_data.append(item)
                elif isinstance(page_data, list):
                    for item in page_data:
                        item_id = item.get("id") or item.get("symbol") or str(item)
                        if item_id not in seen_ids:
                            seen_ids.add(item_id)
                            all_data.append(item)
        except Exception as e:
            print(f"Error fetching size=5: {str(e)}")
        
        # Fetch with size=30
        params_30 = {"size": 30, "type": type, "for": for_category}
        try:
            resp = await client.get(SHAREHUB_OFFERING_URL, params=params_30, headers=DEFAULT_HEADERS)
            if resp.status_code == 200:
                page_data = resp.json()
                if isinstance(page_data, dict) and "data" in page_data:
                    items = page_data.get("data", [])
                    if isinstance(items, list):
                        for item in items:
                            item_id = item.get("id") or item.get("symbol") or str(item)
                            if item_id not in seen_ids:
                                seen_ids.add(item_id)
                                all_data.append(item)
                elif isinstance(page_data, list):
                    for item in page_data:
                        item_id = item.get("id") or item.get("symbol") or str(item)
                        if item_id not in seen_ids:
                            seen_ids.add(item_id)
                            all_data.append(item)
        except Exception as e:
            print(f"Error fetching size=30: {str(e)}")
    
    # Return in the same format as the original API
    return {"success": True, "data": all_data, "total": len(all_data)}

@app.get("/announcements")
async def announcements(page: int = 1, size: int = 12):
    params = {"Page": page, "Size": size}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(SHAREHUB_ANNOUNCEMENT_URL, params=params, headers=DEFAULT_HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch announcements")
    return resp.json()

@app.get("/ipo/general")
async def ipo_general(size: int = 30): return await fetch_offerings(0, 2, size)

@app.get("/ipo/local")
async def ipo_local(size: int = 30): return await fetch_offerings(0, 0, size)

@app.get("/ipo/foreign")
async def ipo_foreign(size: int = 30): return await fetch_offerings(0, 1, size)

@app.get("/right-share")
async def right_share(size: int = 30): return await fetch_offerings(2, 2, size)

@app.get("/fpo")
async def fpo(size: int = 30): return await fetch_offerings(1, 2, size)

@app.get("/mutual-fund-offering")
async def mutual_fund_offering(size: int = 30): return await fetch_offerings(3, 2, size)

@app.get("/debenture-offering")
async def debenture_offering(size: int = 30): return await fetch_offerings(4, 2, size)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

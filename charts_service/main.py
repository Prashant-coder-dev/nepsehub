from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import uvicorn

app = FastAPI(title="NEPSE Charts Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/stock-chart/{symbol}")
async def stock_chart(
    symbol: str, 
    time: str = Query("1Y", regex="^(1D|1W|1M|3M|6M|1Y|5Y)$")
):
    url = f"https://sharehubnepal.com/data/api/v1/price-history/graph/{symbol.upper()}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params={"time": time}, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch price history for {symbol}")
    return resp.json()

@app.get("/stock-chart/index/1D/{symbol}")
async def index_1d_chart(symbol: str):
    url = f"https://sharehubnepal.com/live/api/v1/daily-graph/index/{symbol}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch 1D index graph")
    return resp.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

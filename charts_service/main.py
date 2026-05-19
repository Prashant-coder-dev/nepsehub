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
    if time == "1D":
        url = f"https://sharehubnepal.com/live/api/v1/daily-graph/company/{symbol.upper()}"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    else:
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


@app.get("/symbol-data")
async def symbol_data(symbol: str):
    """
    Fetch historical stock data in OHLCV format for technical analysis.
    """
    symbol_upper = symbol.upper()
    # ShareHub price history for 1Y
    url = f"https://sharehubnepal.com/data/api/v1/price-history/graph/{symbol_upper}"
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, params={"time": "1Y"}, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to history server: {str(e)}")
        
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch historical data for {symbol_upper}")
        
    raw_data = resp.json()
    mapped_candles = []
    
    for d in raw_data:
        t_val = d.get("time") or d.get("date")
        if not t_val: continue
        
        if isinstance(t_val, (int, float)):
            from datetime import datetime
            date_str = datetime.fromtimestamp(t_val).strftime("%Y-%m-%d")
        else:
            date_str = str(t_val).split("T")[0]
            
        mapped_candles.append({
            "Date": date_str,
            "Open": float(d.get("openPrice") or d.get("open") or d.get("contractRate") or d.get("price") or d.get("y") or d.get("value") or 0),
            "High": float(d.get("high") or d.get("highPrice") or d.get("contractRate") or d.get("price") or d.get("y") or d.get("value") or 0),
            "Low": float(d.get("low") or d.get("lowPrice") or d.get("contractRate") or d.get("price") or d.get("y") or d.get("value") or 0),
            "Close": float(d.get("contractRate") or d.get("price") or d.get("close") or d.get("closePrice") or d.get("y") or d.get("value") or 0),
            "Volume": float(d.get("volume") or d.get("vol") or d.get("turnover") or 0)
        })
        
    return {
        "success": True,
        "data": {
            "data": mapped_candles
        }
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

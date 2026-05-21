from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import uvicorn
import sys

# Add shared directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.constants import (
    CDSC_COMPANY_LIST_URL,
    CDSC_CHECK_RESULT_URL
)

app = FastAPI(title="NEPSE IPO Proxy Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IPOCheckRequest(BaseModel):
    companyShareId: int
    boid: str

@app.get("/companies")
async def get_companies():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://iporesult.cdsc.com.np',
        'Referer': 'https://iporesult.cdsc.com.np/'
    }
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(CDSC_COMPANY_LIST_URL, headers=headers)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to CDSC server: {str(e)}")
            
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch companies from CDSC")
        
    return resp.json()

@app.post("/check")
async def check_result(req: IPOCheckRequest):
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://iporesult.cdsc.com.np',
        'Referer': 'https://iporesult.cdsc.com.np/'
    }
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.post(
                CDSC_CHECK_RESULT_URL,
                headers=headers,
                json={"companyShareId": req.companyShareId, "boid": req.boid}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to CDSC check server: {str(e)}")
            
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to check IPO result from CDSC")
        
    return resp.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

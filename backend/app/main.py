import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .models import DCFRequest, RelativeValuationRequest
from .valuation import calculate_dcf, calculate_relative
from .sec_client import get_company, SECError

load_dotenv()

app = FastAPI(
    title="Intrinsic Value Lab API",
    version="1.0.0",
    description="SEC-powered fundamental valuation API for an internship portfolio project.",
)

origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "intrinsic-value-lab-api"}


@app.get("/api/company/{ticker}")
async def company(ticker: str):
    try:
        return await get_company(ticker)
    except SECError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SEC data request failed: {exc}")


@app.post("/api/valuation/dcf")
def dcf(request: DCFRequest):
    try:
        return calculate_dcf(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/valuation/relative")
def relative(request: RelativeValuationRequest):
    return calculate_relative(request.peers)

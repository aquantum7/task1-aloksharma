from pydantic import BaseModel, Field
from typing import List, Optional


class DCFRequest(BaseModel):
    revenue: float = Field(gt=0)
    fcf_margin: float = Field(ge=-1, le=1)
    growth_rate: float = Field(ge=-0.95, le=2)
    wacc: float = Field(gt=0.001, lt=1)
    terminal_growth: float = Field(ge=-0.5, lt=0.5)
    forecast_years: int = Field(ge=1, le=15)
    net_debt: float = 0
    shares: float = Field(gt=0)


class PeerInput(BaseModel):
    name: str
    market_cap: float = Field(ge=0)
    net_income: float = Field(gt=0)
    book_value: float = Field(gt=0)
    enterprise_value: float = Field(ge=0)
    ebitda: float = Field(gt=0)


class RelativeValuationRequest(BaseModel):
    peers: List[PeerInput]

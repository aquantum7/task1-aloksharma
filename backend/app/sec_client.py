import os
import time
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

SEC_BASE = "https://data.sec.gov"
USER_AGENT = os.getenv("SEC_USER_AGENT", "IntrinsicValueLab/1.0 contact@example.com")

_ticker_cache = None
_fact_cache: Dict[str, tuple[float, dict]] = {}
CACHE_SECONDS = 900


class SECError(Exception):
    pass


async def _get(url: str) -> Any:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }
    async with httpx.AsyncClient(timeout=25.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


async def ticker_map():
    global _ticker_cache
    if _ticker_cache is None:
        _ticker_cache = await _get(f"{SEC_BASE}/files/company_tickers.json")
    return _ticker_cache


async def resolve_cik(ticker: str) -> tuple[str, str]:
    data = await ticker_map()
    ticker = ticker.upper().strip()

    for item in data.values():
        if item.get("ticker", "").upper() == ticker:
            return str(item["cik_str"]).zfill(10), item["title"]

    raise SECError(f"Ticker '{ticker}' was not found in the SEC company ticker map.")


async def company_facts(cik: str):
    cached = _fact_cache.get(cik)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]

    data = await _get(f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik}.json")
    _fact_cache[cik] = (time.time(), data)
    return data


async def submissions(cik: str):
    return await _get(f"{SEC_BASE}/submissions/CIK{cik}.json")


def _annual_facts(facts: dict, taxonomy: str, concepts: List[str]) -> List[dict]:
    output = []
    taxonomy_data = facts.get("facts", {}).get(taxonomy, {})

    for concept in concepts:
        units = taxonomy_data.get(concept, {}).get("units", {})
        for unit_values in units.values():
            for fact in unit_values:
                form = fact.get("form")
                fp = fact.get("fp")
                if form == "10-K" and fp == "FY":
                    output.append(fact | {"concept": concept})

    output.sort(key=lambda x: (x.get("end", ""), x.get("filed", "")), reverse=True)
    return output


def latest_annual(facts: dict, concepts: List[str], taxonomy="us-gaap") -> Optional[float]:
    candidates = _annual_facts(facts, taxonomy, concepts)
    if not candidates:
        return None

    # Prefer facts with an annual duration close to a year.
    for item in candidates:
        start = item.get("start")
        end = item.get("end")
        if start and end:
            try:
                from datetime import date
                days = (date.fromisoformat(end) - date.fromisoformat(start)).days
                if 300 <= days <= 380:
                    return float(item["val"])
            except Exception:
                pass
    return float(candidates[0]["val"])


def latest_instant(facts: dict, concepts: List[str], taxonomy="us-gaap") -> Optional[float]:
    taxonomy_data = facts.get("facts", {}).get(taxonomy, {})
    candidates = []

    for concept in concepts:
        units = taxonomy_data.get(concept, {}).get("units", {})
        for unit_values in units.values():
            for fact in unit_values:
                if fact.get("form") in ("10-K", "10-Q") and fact.get("end"):
                    candidates.append(fact)

    candidates.sort(key=lambda x: (x.get("end", ""), x.get("filed", "")), reverse=True)
    return float(candidates[0]["val"]) if candidates else None


def latest_shares(facts: dict) -> Optional[float]:
    taxonomy_data = facts.get("facts", {}).get("dei", {})
    candidates = taxonomy_data.get("EntityCommonStockSharesOutstanding", {}).get("units", {})
    values = []
    for unit_values in candidates.values():
        values.extend(unit_values)
    values.sort(key=lambda x: (x.get("end", ""), x.get("filed", "")), reverse=True)
    return float(values[0]["val"]) if values else None


def filing_list(submission_data: dict, limit=12):
    recent = submission_data.get("filings", {}).get("recent", {})
    rows = []
    for i, form in enumerate(recent.get("form", [])):
        if form not in ("10-K", "10-Q"):
            continue
        accession = recent["accessionNumber"][i]
        primary = recent["primaryDocument"][i]
        cik = submission_data["cik"]
        accession_no_dash = accession.replace("-", "")
        rows.append({
            "form": form,
            "filing_date": recent["filingDate"][i],
            "period": recent["reportDate"][i],
            "accession": accession,
            "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dash}/{primary}",
        })
        if len(rows) >= limit:
            break
    return rows


async def get_company(ticker: str):
    cik, title = await resolve_cik(ticker)
    facts = await company_facts(cik)
    submission_data = await submissions(cik)

    revenue = latest_annual(facts, [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ])

    net_income = latest_annual(facts, [
        "NetIncomeLoss",
        "ProfitLoss",
    ])

    cfo = latest_annual(facts, [
        "NetCashProvidedByUsedInOperatingActivities",
    ])

    capex = latest_annual(facts, [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ])

    cash = latest_instant(facts, [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ])

    debt = latest_instant(facts, [
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "LongTermDebtCurrent",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndFinanceLeaseObligations",
    ])

    equity = latest_instant(facts, [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ])

    shares = latest_shares(facts)

    return {
        "ticker": ticker.upper(),
        "company": title,
        "cik": cik,
        "financials": {
            "revenue": revenue,
            "net_income": net_income,
            "operating_cash_flow": cfo,
            "capital_expenditures": capex,
            "cash": cash,
            "debt": debt,
            "equity": equity,
            "shares": shares,
            "fcf_proxy": (cfo - capex) if cfo is not None and capex is not None else None,
        },
        "filings": filing_list(submission_data),
        "source": "U.S. Securities and Exchange Commission EDGAR / XBRL",
    }

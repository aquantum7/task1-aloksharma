# Intrinsic Value Lab

A full-stack finance research application built for a Full Stack Development Internship project.

**Goal:** estimate the intrinsic mathematical value of a public company using financial information sourced from official SEC filings, then compare relative valuation multiples such as P/E, P/B, and EV/EBITDA.

> Educational project only. This application is not investment advice.

## What this project demonstrates

- React + Vite frontend
- FastAPI + Python backend
- REST API design
- SEC EDGAR company submissions and XBRL Company Facts APIs
- Financial-statement data normalization
- DCF valuation
- P/E, P/B and EV/EBITDA calculations
- Peer-company comparison
- Responsive dashboard UI
- Validation and error handling
- Environment configuration
- Clean separation between frontend, backend and valuation logic

## Architecture

```text
React/Vite
   |
   | HTTP / JSON
   v
FastAPI backend
   |
   +--> SEC EDGAR Submissions API
   |
   +--> SEC XBRL Company Facts API
   |
   v
Normalized financial metrics
   |
   +--> DCF engine
   |
   +--> Relative valuation engine
```

## SEC data source

The backend uses official SEC EDGAR APIs:

- `https://data.sec.gov/submissions/CIK##########.json`
- `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`

The SEC states that these APIs provide filing history and extracted XBRL data and do not require API keys. Automated access must follow SEC fair-access requirements.

The app therefore requires a descriptive `SEC_USER_AGENT`, for example:

```env
SEC_USER_AGENT=YourName your-email@example.com
```

Do not use a fake identity or impersonate another organization.

## Features

### 1. SEC company lookup

Enter a ticker such as `AAPL`, `MSFT`, `GOOGL`, or another U.S.-listed SEC filer.

The backend:

1. Resolves ticker -> CIK using SEC's company ticker mapping.
2. Retrieves company facts.
3. Selects standardized US-GAAP concepts.
4. Extracts annual revenue, net income, operating cash flow, capital expenditures, cash, debt, equity and shares where available.
5. Returns recent 10-K/10-Q filing links.

### 2. DCF model

The user can adjust:

- Revenue growth
- FCF margin
- WACC
- Terminal growth
- Forecast years
- Net debt
- Diluted shares

The model calculates:

```text
Revenue_t = Revenue_(t-1) × (1 + growth)

FCF_t = Revenue_t × FCF margin

PV(FCF_t) = FCF_t / (1 + WACC)^t

Terminal Value = FCF_n × (1 + g) / (WACC - g)

Enterprise Value = Σ PV(FCF) + PV(Terminal Value)

Equity Value = Enterprise Value - Net Debt

Intrinsic Value / Share = Equity Value / Shares
```

### 3. Relative valuation

For each peer:

```text
P/E = Market Cap / Net Income
P/B = Market Cap / Book Value
EV/EBITDA = Enterprise Value / EBITDA
```

Market price / market capitalization is intentionally treated as market data rather than pretending it came from an SEC filing.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env
# macOS/Linux: cp .env.example .env

uvicorn app.main:app --reload --port 8000
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally:

```text
http://localhost:5173
```

The frontend expects the API at:

```text
http://localhost:8000
```

You can change it with:

```env
VITE_API_URL=http://localhost:8000
```

## API endpoints

### Health

`GET /api/health`

### Company fundamentals

`GET /api/company/{ticker}`

Example:

```text
GET /api/company/AAPL
```

### DCF

`POST /api/valuation/dcf`

### Relative valuation

`POST /api/valuation/relative`

### Recent filings

Returned as part of the company endpoint.

## Important implementation notes

SEC `data.sec.gov` does not provide browser CORS access for direct frontend calls, so SEC requests are deliberately made by the backend.

The application caches company facts in memory for a short period to reduce repeated SEC requests.

XBRL taxonomy labels can differ between companies. The extraction layer therefore checks multiple standard concepts and selects the most recent suitable annual value.

## Project structure

```text
intrinsic-value-lab/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── sec_client.py
│   │   ├── models.py
│   │   ├── valuation.py
│   │   └── __init__.py
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Suggested GitHub setup

```bash
git init
git add .
git commit -m "Initial full-stack intrinsic value lab"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/intrinsic-value-lab.git
git push -u origin main
```

## Internship presentation points

You can explain the project in five parts:

1. **Problem:** stock prices can be influenced by market sentiment, while business fundamentals are reported in filings.
2. **Data:** SEC EDGAR provides official filing and XBRL data.
3. **Backend:** FastAPI normalizes raw XBRL facts into usable financial metrics.
4. **Valuation:** the DCF estimates present value of projected free cash flows; relative valuation compares standard multiples.
5. **Frontend:** React provides an interactive research dashboard where assumptions can be changed without modifying the backend.

## Limitations

This is a learning project, not a professional valuation system. Real-world analysis may require segment-level modeling, working-capital forecasts, stock-based compensation treatment, leases, minority interests, pension obligations, cyclicality, scenario analysis, and careful accounting judgment.

Market price inputs are user-supplied because the project is intentionally centered on SEC filing data for business fundamentals rather than introducing an unrelated market-data provider.

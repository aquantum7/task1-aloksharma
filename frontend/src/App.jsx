import { useMemo, useState } from "react";
import { BarChart3, Database, FileText, Calculator, Search, ExternalLink, RefreshCw } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const money = (v) => v == null ? "—" : new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
  notation: Math.abs(v) >= 1e9 ? "compact" : "standard"
}).format(v);

const pct = (v) => `${(v * 100).toFixed(1)}%`;
const multiple = (v) => v == null ? "—" : `${v.toFixed(2)}x`;

function App() {
  const [ticker, setTicker] = useState("AAPL");
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [assumptions, setAssumptions] = useState({
    growth_rate: 0.08,
    fcf_margin: 0.22,
    wacc: 0.09,
    terminal_growth: 0.03,
    forecast_years: 5
  });

  const [sharePrice, setSharePrice] = useState(200);
  const [dcf, setDcf] = useState(null);

  const loadCompany = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/api/company/${ticker}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to load company.");
      setCompany(data);
      setSharePrice(sharePrice || 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runDCF = async () => {
    if (!company?.financials) return;
    const f = company.financials;
    const revenue = f.revenue || 0;
    const shares = f.shares || 1;
    const netDebt = (f.debt || 0) - (f.cash || 0);

    try {
      const response = await fetch(`${API}/api/valuation/dcf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          revenue,
          shares,
          net_debt: netDebt,
          ...assumptions
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "DCF calculation failed.");
      setDcf(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const impliedMarketCap = useMemo(() => {
    if (!company?.financials?.shares) return null;
    return sharePrice * company.financials.shares;
  }, [sharePrice, company]);

  const valuationGap = useMemo(() => {
    if (!dcf?.intrinsic_value_per_share || !sharePrice) return null;
    return dcf.intrinsic_value_per_share / sharePrice - 1;
  }, [dcf, sharePrice]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><BarChart3 size={20}/></div>
          <div>
            <div className="brand-name">Intrinsic Value Lab</div>
            <div className="brand-sub">SEC-first fundamental research</div>
          </div>
        </div>
        <div className="source-pill"><Database size={14}/> Official SEC EDGAR data</div>
      </header>

      <main className="container">
        <section className="hero">
          <div>
            <p className="eyebrow">FULL-STACK FINANCE PROJECT</p>
            <h1>Separate the business<br/>from the stock hype.</h1>
            <p className="hero-copy">
              Pull reported fundamentals from SEC filings, model future free cash flow,
              and compare valuation multiples across peers.
            </p>
          </div>
          <div className="hero-card">
            <div className="mini-label">Research workflow</div>
            <div className="workflow">
              <span>SEC filing</span><b>→</b><span>Normalize</span><b>→</b><span>DCF</span><b>→</b><span>Compare</span>
            </div>
          </div>
        </section>

        <section className="search-panel">
          <div>
            <div className="section-kicker">COMPANY EXPLORER</div>
            <h2>Start with an SEC filer</h2>
          </div>
          <div className="search-row">
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && loadCompany()}
              placeholder="Ticker e.g. AAPL"
            />
            <button onClick={loadCompany} disabled={loading}>
              {loading ? <RefreshCw className="spin" size={17}/> : <Search size={17}/>}
              {loading ? "Loading" : "Analyze"}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
        </section>

        {!company ? (
          <section className="empty">
            <FileText size={34}/>
            <h3>Enter a ticker to load filing data</h3>
            <p>Try AAPL, MSFT, GOOGL, AMZN or another SEC-reporting company.</p>
          </section>
        ) : (
          <>
            <section className="company-heading">
              <div>
                <div className="ticker">{company.ticker}</div>
                <h2>{company.company}</h2>
                <span className="muted">CIK {company.cik} · {company.source}</span>
              </div>
              <div className="market-input">
                <label>Current share price</label>
                <div className="price-input"><span>$</span><input type="number" value={sharePrice} onChange={e => setSharePrice(Number(e.target.value))}/></div>
                <small>User supplied market input</small>
              </div>
            </section>

            <section className="metric-grid">
              <Metric label="Revenue" value={money(company.financials.revenue)}/>
              <Metric label="Net income" value={money(company.financials.net_income)}/>
              <Metric label="Operating cash flow" value={money(company.financials.operating_cash_flow)}/>
              <Metric label="FCF proxy" value={money(company.financials.fcf_proxy)}/>
              <Metric label="Cash" value={money(company.financials.cash)}/>
              <Metric label="Debt" value={money(company.financials.debt)}/>
            </section>

            <div className="two-col">
              <section className="card">
                <div className="card-title"><Calculator size={18}/> DCF assumptions</div>
                <div className="form-grid">
                  <Field label="Revenue growth" value={assumptions.growth_rate} display={pct(assumptions.growth_rate)} step="0.01" onChange={v => setAssumptions({...assumptions, growth_rate:v})}/>
                  <Field label="FCF margin" value={assumptions.fcf_margin} display={pct(assumptions.fcf_margin)} step="0.01" onChange={v => setAssumptions({...assumptions, fcf_margin:v})}/>
                  <Field label="WACC" value={assumptions.wacc} display={pct(assumptions.wacc)} step="0.005" onChange={v => setAssumptions({...assumptions, wacc:v})}/>
                  <Field label="Terminal growth" value={assumptions.terminal_growth} display={pct(assumptions.terminal_growth)} step="0.005" onChange={v => setAssumptions({...assumptions, terminal_growth:v})}/>
                  <Field label="Forecast years" value={assumptions.forecast_years} display={`${assumptions.forecast_years} years`} step="1" min="1" max="15" onChange={v => setAssumptions({...assumptions, forecast_years:v})}/>
                </div>
                <button className="primary full" onClick={runDCF}>Run DCF model</button>
              </section>

              <section className="card result-card">
                <div className="card-title">Intrinsic value output</div>
                {dcf ? (
                  <>
                    <div className="big-number">${dcf.intrinsic_value_per_share.toFixed(2)}</div>
                    <div className="muted">Estimated intrinsic value per share</div>
                    <div className="comparison">
                      <div><span>Market price</span><strong>${sharePrice.toFixed(2)}</strong></div>
                      <div><span>DCF / market</span><strong>{pct(dcf.intrinsic_value_per_share / sharePrice - 1)}</strong></div>
                    </div>
                    <div className="chart">
                      <ResponsiveContainer width="100%" height={210}>
                        <LineChart data={dcf.forecast}>
                          <XAxis dataKey="year" tickLine={false} axisLine={false}/>
                          <YAxis tickFormatter={v => `$${money(v)}`} tickLine={false} axisLine={false}/>
                          <Tooltip formatter={(v) => [`$${money(v)}`, "FCF"]}/>
                          <Line type="monotone" dataKey="fcf" strokeWidth={3} dot={false}/>
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </>
                ) : (
                  <div className="result-placeholder">Run the model to see projected FCF, terminal value, enterprise value and implied per-share value.</div>
                )}
              </section>
            </div>

            <section className="card">
              <div className="card-head">
                <div>
                  <div className="card-title"><BarChart3 size={18}/> Relative valuation</div>
                  <p className="muted">Add peer market data to compare P/E, P/B and EV/EBITDA.</p>
                </div>
              </div>
              <PeerTable company={company}/>
            </section>

            <section className="card filings">
              <div className="card-title"><FileText size={18}/> Recent SEC filings</div>
              <div className="filing-list">
                {company.filings.map((f) => (
                  <a key={f.accession} href={f.url} target="_blank" rel="noreferrer">
                    <div className="filing-form">{f.form}</div>
                    <div><strong>{f.period || f.filing_date}</strong><small>Filed {f.filing_date}</small></div>
                    <ExternalLink size={16}/>
                  </a>
                ))}
              </div>
            </section>
          </>
        )}

        <footer>
          <span>Intrinsic Value Lab · Internship Portfolio Project</span>
          <span>Fundamentals from SEC EDGAR · Market inputs are user supplied</span>
        </footer>
      </main>
    </div>
  );
}

function Metric({label, value}) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>
}

function Field({label, value, display, onChange, ...props}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="number" value={value} onChange={e => onChange(Number(e.target.value))} {...props}/>
      <em>{display}</em>
    </label>
  )
}

function PeerTable({company}) {
  const [rows, setRows] = useState([
    {name: company.ticker, market_cap: 0, net_income: company.financials.net_income || 1, book_value: company.financials.equity || 1, enterprise_value: 0, ebitda: 1},
    {name: "Peer A", market_cap: 0, net_income: 1, book_value: 1, enterprise_value: 0, ebitda: 1},
    {name: "Peer B", market_cap: 0, net_income: 1, book_value: 1, enterprise_value: 0, ebitda: 1}
  ]);
  const [result, setResult] = useState(null);

  const update = (i, key, value) => {
    const copy = [...rows];
    copy[i] = {...copy[i], [key]: key === "name" ? value : Number(value)};
    setRows(copy);
  };

  const calculate = async () => {
    const response = await fetch(`${API}/api/valuation/relative`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({peers: rows})
    });
    setResult(await response.json());
  };

  return (
    <>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Company</th><th>Market cap</th><th>Net income</th><th>Book value</th><th>EV</th><th>EBITDA</th></tr></thead>
          <tbody>
            {rows.map((r,i) => <tr key={i}>
              {["name","market_cap","net_income","book_value","enterprise_value","ebitda"].map(k =>
                <td key={k}><input className="table-input" type={k==="name"?"text":"number"} value={r[k]} onChange={e=>update(i,k,e.target.value)}/></td>
              )}
            </tr>)}
          </tbody>
        </table>
      </div>
      <button className="secondary" onClick={calculate}>Calculate multiples</button>
      {result && <div className="multiple-grid">
        {result.peers.map(p => <div className="multiple-card" key={p.name}><strong>{p.name}</strong><span>P/E {multiple(p.pe)}</span><span>P/B {multiple(p.pb)}</span><span>EV/EBITDA {multiple(p.ev_ebitda)}</span></div>)}
      </div>}
    </>
  );
}

export default App;

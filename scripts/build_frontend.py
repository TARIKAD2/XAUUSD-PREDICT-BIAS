import os

components_dir = "frontend/components"
app_dir = "frontend/app"

components = {
    "MarketCard.js": """
export default function MarketCard({ item }) {
  if (!item) return null;
  const isUp = item.change >= 0;
  return (
    <div className="card market-card">
      <h3>{item.symbol}</h3>
      <p className="price">${item.close?.toFixed(4)}</p>
      <p className={`change ${isUp ? 'up' : 'down'}`}>
        {isUp ? '▲' : '▼'} {Math.abs(item.change)?.toFixed(2)}%
      </p>
    </div>
  );
}
""",
    "PredictionCard.js": """
import ProbabilityBar from './ProbabilityBar';
import ConfidenceBadge from './ConfidenceBadge';

export default function PredictionCard({ prediction }) {
  if (!prediction) return null;
  return (
    <div className="card prediction-card">
      <h3>AI Prediction: {prediction.symbol}</h3>
      <ConfidenceBadge confidence={prediction.confidence} />
      <p>Direction: <strong>{prediction.direction}</strong></p>
      <ProbabilityBar probabilities={prediction.probabilities} />
      <div className="reasons">
        <h4>Top Features:</h4>
        <ul>
          {prediction.top_features?.map(f => (
            <li key={f.feature}>{f.feature}: {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(4)}</li>
          ))}
        </ul>
      </div>
      <p className="model-info">Model: {prediction.model} ({prediction.model_version})</p>
    </div>
  );
}
""",
    "NewsCard.js": """
export default function NewsCard({ item }) {
  return (
    <div className="card news-card">
      <h4><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></h4>
      <p className="source">{item.source} • {new Date(item.published_at).toLocaleString()}</p>
      <p className="sentiment">Sentiment: {item.sentiment}</p>
    </div>
  );
}
""",
    "EconomicEventCard.js": """
export default function EconomicEventCard({ item }) {
  return (
    <div className="card event-card">
      <h4>{item.title}</h4>
      <p>{new Date(item.timestamp).toLocaleString()}</p>
      <p>Actual: {item.actual} | Forecast: {item.forecast}</p>
      <p>Importance: {item.importance}</p>
    </div>
  );
}
""",
    "ProbabilityBar.js": """
export default function ProbabilityBar({ probabilities }) {
  if (!probabilities) return null;
  return (
    <div className="probability-bar-container">
      <div className="probability-bar">
        <div className="bar bullish" style={{width: `${probabilities.bullish * 100}%`}}></div>
        <div className="bar neutral" style={{width: `${probabilities.neutral * 100}%`}}></div>
        <div className="bar bearish" style={{width: `${probabilities.bearish * 100}%`}}></div>
      </div>
      <div className="labels">
        <span>Bullish: {(probabilities.bullish * 100).toFixed(1)}%</span>
        <span>Neutral: {(probabilities.neutral * 100).toFixed(1)}%</span>
        <span>Bearish: {(probabilities.bearish * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
""",
    "ConfidenceBadge.js": """
export default function ConfidenceBadge({ confidence }) {
  let level = 'low';
  if (confidence > 0.7) level = 'high';
  else if (confidence > 0.5) level = 'medium';
  return <span className={`badge confidence-${level}`}>Confidence: {(confidence * 100).toFixed(1)}%</span>;
}
""",
    "StatusPanel.js": """
export default function StatusPanel({ title, message, type = 'info' }) {
  return (
    <div className={`status-panel ${type}`}>
      <h4>{title}</h4>
      <p>{message}</p>
    </div>
  );
}
"""
}

page_js = """
"use client";
import { useEffect, useState } from "react";
import { api } from "../services/api";
import StatusPanel from "../components/StatusPanel";
import MarketCard from "../components/MarketCard";
import PredictionCard from "../components/PredictionCard";
import NewsCard from "../components/NewsCard";
import EconomicEventCard from "../components/EconomicEventCard";

const assets = ["XAUUSD", "US100", "EURUSD", "DXY", "GBPUSD", "USDJPY"];

function load(f, s) {
  f().then(x => s({ data: x })).catch(e => s({ error: e }));
}

export default function Home() {
  const [a, setA] = useState("XAUUSD");
  const [m, setM] = useState({});
  const [n, setN] = useState({});
  const [e, setE] = useState({});
  const [p, setP] = useState({});
  const [perf, setPerf] = useState({});

  useEffect(() => {
    load(api.market, setM);
    load(api.news, setN);
    load(api.events, setE);
    load(api.performance, setPerf);
    load(() => api.prediction(a), setP);
  }, [a]);

  return (
    <main className="container">
      <header>
        <h1>AI Market Intelligence</h1>
        <p>Research only — no automatic execution or guaranteed outcomes.</p>
      </header>

      <section className="controls">
        <label>Select Asset: </label>
        <select value={a} onChange={x => setA(x.target.value)}>
          {assets.map(x => <option key={x} value={x}>{x}</option>)}
        </select>
      </section>

      <section className="dashboard-grid">
        <div className="col">
          <h2>AI Prediction</h2>
          {p.data ? <PredictionCard prediction={p.data} /> : <StatusPanel title="AI Prediction" message={p.error?.message || "Loading…"} />}
        </div>
        <div className="col">
          <h2>Model Performance</h2>
          {perf.data ? <pre>{JSON.stringify(perf.data, null, 2)}</pre> : <StatusPanel title="Model Performance" message={perf.error?.message || "Loading performance…"} />}
        </div>
      </section>

      <section>
        <h2>Market Overview</h2>
        {m.data ? (
          <div className="grid">
            {m.data.items?.map(x => <MarketCard key={x.symbol} item={x} />)}
          </div>
        ) : (
          <StatusPanel title="Market data" message={m.error?.message || "Loading verified data…"} />
        )}
      </section>

      <section className="dashboard-grid">
        <div className="col">
          <h2>News</h2>
          {n.data ? (
            <div className="grid-col">
              {n.data.items?.map(x => <NewsCard key={x.url} item={x} />)}
            </div>
          ) : (
            <StatusPanel title="News" message={n.error?.message || "Loading verified news…"} />
          )}
        </div>
        <div className="col">
          <h2>Economic Calendar</h2>
          {e.data ? (
            <div className="grid-col">
              {e.data.items?.map((x, i) => <EconomicEventCard key={i} item={x} />)}
            </div>
          ) : (
            <StatusPanel title="Economic events" message={e.error?.message || "Loading verified events…"} />
          )}
        </div>
      </section>
    </main>
  );
}
"""

globals_css = """
:root {
  --bg: #f8f9fa;
  --text: #212529;
  --card-bg: #ffffff;
  --border: #dee2e6;
  --primary: #0d6efd;
  --success: #198754;
  --danger: #dc3545;
  --warning: #ffc107;
  --info: #0dcaf0;
}

body {
  background-color: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  margin: 0;
  padding: 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

header {
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
}

.controls {
  margin-bottom: 2rem;
}

.controls select {
  padding: 0.5rem;
  font-size: 1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.grid-col {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.card h3, .card h4 {
  margin-top: 0;
}

.up { color: var(--success); }
.down { color: var(--danger); }

.probability-bar-container {
  margin: 1rem 0;
}

.probability-bar {
  display: flex;
  height: 20px;
  border-radius: 10px;
  overflow: hidden;
  background: #eee;
}

.bar.bullish { background: var(--success); }
.bar.neutral { background: var(--warning); }
.bar.bearish { background: var(--danger); }

.labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}
.confidence-high { background: var(--success); color: white; }
.confidence-medium { background: var(--warning); color: black; }
.confidence-low { background: var(--danger); color: white; }

.status-panel {
  padding: 1rem;
  border-radius: 8px;
  background: #e9ecef;
  border: 1px solid #ced4da;
}
"""

api_js = """
const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get(path) {
  const r = await fetch(base + path);
  const b = await r.json().catch(() => ({}));
  if (!r.ok) throw Error(b.error?.message || `API ${r.status}`);
  return b;
}

export const api = {
  health: () => get("/api/health"),
  market: () => get("/api/market"),
  prediction: (s) => get(`/api/predictions/${s}`),
  news: () => get("/api/news"),
  events: () => get("/api/economic-events"),
  performance: () => get("/api/model-performance")
};
"""

os.makedirs(components_dir, exist_ok=True)
for name, content in components.items():
    with open(os.path.join(components_dir, name), 'w', encoding='utf-8') as f:
        f.write(content.strip())

with open(os.path.join(app_dir, "page.js"), 'w', encoding='utf-8') as f:
    f.write(page_js.strip())

os.makedirs("frontend/styles", exist_ok=True)
with open("frontend/styles/globals.css", 'w', encoding='utf-8') as f:
    f.write(globals_css.strip())

# Make sure layout.js imports globals.css
layout_js = """
import '../styles/globals.css'

export const metadata = {
  title: 'AI Market Intelligence',
  description: 'Financial market intelligence and machine-learning research platform',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
"""
with open(os.path.join(app_dir, "layout.js"), 'w', encoding='utf-8') as f:
    f.write(layout_js.strip())

with open("frontend/services/api.js", 'w', encoding='utf-8') as f:
    f.write(api_js.strip())

print("Frontend setup complete!")


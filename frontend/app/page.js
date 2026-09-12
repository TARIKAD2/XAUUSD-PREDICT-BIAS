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
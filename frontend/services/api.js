const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get(path) {
  const r = await fetch(base + path);
  const b = await r.json().catch(() => ({}));
  if (!r.ok) throw Error(b.error?.message || `API ${r.status}`);
  return b;
}

export const POLLING_INTERVAL_MS = 15000;

export const api = {
  health: () => get("/api/health"),
  market: () => get("/api/market"),
  marketSymbol: (s) => get(`/api/market/${s}`),
  prediction: (s) => get(`/api/predictions/${s}?horizon=daily`),
  predictionWeekly: (s) => get(`/api/predictions/${s}?horizon=weekly`),
  explanation: (s) => get(`/api/explanations/${s}`),
  news: (s) => get(s ? `/api/news?symbol=${s}` : "/api/news"),
  events: (mode = "today") => get(`/api/economic-events?mode=${mode}`),
  performance: () => get("/api/model-performance"),
  quality: () => get("/api/data-quality"),
};
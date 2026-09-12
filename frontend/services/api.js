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
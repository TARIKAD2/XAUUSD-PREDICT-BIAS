"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "../context/LanguageContext";

function parseProviderTimestampMs(tick) {
  if (!tick) return null;
  const ts = tick.provider_timestamp ?? tick.provider_time ?? tick.iso_timestamp ?? tick.timestamp;
  if (ts == null || ts === "") return null;
  if (typeof ts === "number") {
    return Number.isFinite(ts) ? (ts > 1e11 ? ts : ts * 1000) : null;
  }
  if (typeof ts === "string") {
    const trimmed = ts.trim();
    if (!trimmed) return null;
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      const num = Number(trimmed);
      return Number.isFinite(num) ? (num > 1e11 ? num : num * 1000) : null;
    }
    let isoStr = trimmed;
    if (isoStr.includes(" ") && !isoStr.includes("T")) {
      isoStr = isoStr.replace(" ", "T");
    }
    if (!isoStr.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(isoStr)) {
      isoStr += "Z";
    }
    const parsed = new Date(isoStr).getTime();
    return isNaN(parsed) ? null : parsed;
  }
  return null;
}

function parseReceivedTimestampMs(tick) {
  if (!tick) return null;
  const ts = tick.received_at ?? tick.browser_received_at ?? tick.received_timestamp;
  if (ts == null || ts === "") return null;
  if (typeof ts === "number") {
    return Number.isFinite(ts) ? (ts > 1e11 ? ts : ts * 1000) : null;
  }
  if (typeof ts === "string") {
    const trimmed = ts.trim();
    if (!trimmed) return null;
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      const num = Number(trimmed);
      return Number.isFinite(num) ? (num > 1e11 ? num : num * 1000) : null;
    }
    const parsed = new Date(trimmed).getTime();
    return isNaN(parsed) ? null : parsed;
  }
  return null;
}

export default function MarketCard({ item, liveTick, wsStatus }) {
  const { t } = useTranslation();
  const [now, setNow] = useState(() => Date.now());

  // Periodically re-evaluate actual current delay and freshness
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(Date.now());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  if (!item) return null;

  const symbol = item.symbol || "XAUUSD";

  // Real price (live tick price preferred, falling back to verified candle/market item price, never fake)
  const rawPrice = liveTick?.price ?? liveTick?.close ?? item.price ?? item.close ?? null;
  const priceFormatted = typeof rawPrice === "number"
    ? rawPrice.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 })
    : "—";

  // Real change metrics (never fake -0.64 / -22.27)
  const changePct = item.daily_change_percent ?? item.change ?? null;
  const hasChange = typeof changePct === "number";
  const isUp = hasChange ? changePct >= 0 : true;

  let pointsChange = item.points_change ?? null;
  if (pointsChange == null && hasChange && typeof rawPrice === "number") {
    const prevClose = rawPrice / (1 + changePct / 100);
    pointsChange = rawPrice - prevClose;
  }

  // Parse exact timestamps
  const provMs = parseProviderTimestampMs(liveTick);
  const recvMs = parseReceivedTimestampMs(liveTick);

  // Connection state
  const currentWsStatus = wsStatus || "DISCONNECTED";
  const isWsConnected = currentWsStatus === "CONNECTED";

  // Calculate truthful delay and freshness
  let latencyMs = null;
  let feedStatus = "OFFLINE";

  if (provMs !== null) {
    latencyMs = Math.max(0, now - provMs);
    if (isWsConnected) {
      const ageSec = latencyMs / 1000;
      if (ageSec < 5) {
        feedStatus = "LIVE";
      } else if (ageSec <= 30) {
        feedStatus = "DELAYED";
      } else {
        feedStatus = "STALE";
      }
    } else {
      feedStatus = "OFFLINE";
    }
  } else {
    feedStatus = "OFFLINE";
  }

  const tickLatencyDisplay = latencyMs !== null ? `${latencyMs} ms` : "N/A";
  const providerTimeDisplay = provMs !== null ? new Date(provMs).toLocaleTimeString() : "N/A";
  const wsReceivedDisplay = recvMs !== null ? new Date(recvMs).toLocaleTimeString() : "N/A";

  // Color mapping
  const statusColor = {
    LIVE: "var(--bullish)",
    DELAYED: "var(--warning)",
    STALE: "#f87171",
    OFFLINE: "var(--bearish)",
  }[feedStatus] || "var(--text-muted)";

  const wsColor = {
    CONNECTED: "var(--bullish)",
    CONNECTING: "var(--warning)",
    RECONNECTING: "var(--warning)",
    DISCONNECTED: "var(--bearish)",
  }[currentWsStatus] || "var(--text-muted)";

  return (
    <div className="hero-ticker-container">
      <div className="hero-ticker-top">
        <div className="hero-symbol-group">
          <span className="hero-symbol-title">{symbol}</span>
          <span className="hero-symbol-subtitle">{t("market.spot_gold_usd") || "Spot Gold / US Dollar"}</span>
          <span className="hero-badge-pill">{t("market.live_ws") || "Twelve Data Live WebSocket"}</span>
        </div>
        <span className={`hero-live-badge ${feedStatus.toLowerCase()}`}>
          ● {feedStatus}
        </span>
      </div>

      <div className="hero-price-row">
        <div className="hero-price-display">{priceFormatted}</div>
        {hasChange && (
          <div className={`hero-change-badge ${isUp ? "up" : "down"}`}>
            {isUp ? "▲" : "▼"} {Math.abs(changePct).toFixed(2)}%
            {pointsChange != null ? ` (${pointsChange > 0 ? "+" : ""}${pointsChange.toFixed(2)} pts)` : ""}
          </div>
        )}
      </div>

      <div className="hero-metrics-grid">
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.feed_status") || "FEED STATUS"}</span>
          <span className="hero-metric-value" style={{ color: statusColor, fontWeight: 700 }}>
            {feedStatus}
          </span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.tick_latency") || "TICK LATENCY"}</span>
          <span className="hero-metric-value">{tickLatencyDisplay}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.provider_time") || "PROVIDER TIME"}</span>
          <span className="hero-metric-value">{providerTimeDisplay}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.ws_received") || "WS RECEIVED"}</span>
          <span className="hero-metric-value">{wsReceivedDisplay}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.ws_state") || "WS STATE"}</span>
          <span className="hero-metric-value" style={{ color: wsColor }}>
            {currentWsStatus}
          </span>
        </div>
      </div>
    </div>
  );
}
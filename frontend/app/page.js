"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { useTranslation } from "../context/LanguageContext";
import { api, POLLING_INTERVAL_MS } from "../services/api";
import StatusPanel from "../components/StatusPanel";
import LanguageSwitcher from "../components/LanguageSwitcher";
import MarketCard from "../components/MarketCard";
import PriceChart from "../components/PriceChart";
import PredictionCard from "../components/PredictionCard";
import TechnicalPanel from "../components/TechnicalPanel";
import ScenarioPanel from "../components/ScenarioPanel";
import ExplanationPanel from "../components/ExplanationPanel";
import { liveMarket } from "../services/liveMarket";

const asset = "XAUUSD";

function load(fetcher, setter) {
  setter({ loading: true });
  fetcher()
    .then((data) => setter({ data, loading: false }))
    .catch((error) => setter({ error, loading: false }));
}

function refreshData(fetcher, setter) {
  return fetcher()
    .then((data) => {
      setter((prev) => ({ ...prev, data, error: null, loading: false }));
    })
    .catch((error) => {
      setter((prev) => (prev.data ? prev : { error, loading: false }));
    });
}

function statusLabel(t, value, fallbackKey = "online") {
  const normalized = String(value || "").toLowerCase().replace(/[\s-]+/g, "_");
  const keys = {
    online: "online",
    ok: "online",
    healthy: "online",
    connected: "connected",
    connecting: "connecting",
    reconnecting: "reconnecting",
    offline: "offline",
    stale: "stale",
    fresh: "fresh",
    nominal: "nominal",
    degraded: "degraded",
    error: "error",
    good: "online",
    valid: "fresh",
  };
  return t(`status.${keys[normalized] || fallbackKey}`);
}

function PanelContent({ title, state, empty, children }) {
  const { t } = useTranslation();
  if (state?.loading || (!state?.data && !state?.error)) {
    return <StatusPanel title={title} message={t("status_panel.loading_telemetry")} />;
  }
  if (state?.error) {
    return <StatusPanel title={title} message={state.error.message || t("status_panel.unavailable")} type="error" />;
  }
  if (empty) {
    return <StatusPanel title={title} message={t("status_panel.no_records")} />;
  }
  return children;
}

export default function Home() {
  const { t, locale } = useTranslation();
  const [health, setHealth] = useState({});
  const [market, setMarket] = useState({});
  const [detail, setDetail] = useState({});
  const [prediction, setPrediction] = useState({});
  const [predictionWeekly, setPredictionWeekly] = useState({});
  const [predictionHorizon, setPredictionHorizon] = useState("daily");
  const [explanation, setExplanation] = useState({});
  const [liveTick, setLiveTick] = useState(null);
  const [wsStatus, setWsStatus] = useState("CONNECTING");

  const refreshingRef = useRef(false);

  // Subscribe to WebSocket live tick stream
  useEffect(() => {
    const unsubscribe = liveMarket.subscribe((tick, status) => {
      if (status) {
        setWsStatus(status);
      }
      if (tick && (tick.type === "price" || tick.event === "price" || tick.type === "initial_state")) {
        const sym = (tick.symbol || tick.normalized_symbol || "").replace("/", "").toUpperCase();
        if (sym === "XAUUSD") {
          setLiveTick(tick);
        }
      }
    });
    return () => {
      unsubscribe();
    };
  }, []);

  // Polling refresher for background REST data
  const refreshLive = useCallback(async () => {
    if (refreshingRef.current) return;
    if (typeof document !== "undefined" && document.hidden) return;
    refreshingRef.current = true;
    try {
      await Promise.allSettled([
        refreshData(api.market, setMarket),
        refreshData(() => api.marketSymbol(asset), setDetail),
        refreshData(() => api.prediction(asset), setPrediction),
        refreshData(() => api.predictionWeekly(asset), setPredictionWeekly),
        refreshData(() => api.explanation(asset), setExplanation),
        refreshData(api.health, setHealth),
      ]);
    } finally {
      refreshingRef.current = false;
    }
  }, []);

  // Initial load
  useEffect(() => {
    load(api.health, setHealth);
    load(api.market, setMarket);
    load(() => api.marketSymbol(asset), setDetail);
    load(() => api.prediction(asset), setPrediction);
    load(() => api.predictionWeekly(asset), setPredictionWeekly);
    load(() => api.explanation(asset), setExplanation);
  }, []);

  // Interval polling for background candles and predictions
  useEffect(() => {
    if (POLLING_INTERVAL_MS <= 0) return;
    const intervalId = setInterval(() => {
      refreshLive();
    }, POLLING_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [refreshLive]);

  const selectedMarket = market.data?.items?.find((item) => item.symbol === asset);
  const candles = detail.data?.candles || [];
  const freshnessText = prediction.data?.data_quality || (selectedMarket ? (selectedMarket.is_stale ? "STALE" : "FRESH") : "NOMINAL");

  return (
    <main className="terminal-wrapper">
      {/* Top Header Bar */}
      <header className="terminal-header-bar">
        <div className="brand-section">
          <span className="brand-symbol-tag">XAU/USD</span>
          <div className="brand-title-group">
            <h1>
              {t("brand.title")}
              <span className="brand-subtitle">
                {t("brand.subtitle")}
              </span>
            </h1>
          </div>
        </div>

        <div className="header-tools">
          <div className="system-status-ribbon">
            <div className="status-chip good">
              <span className="pulse-dot green" />
              {t("status.api")}: <strong>{health.loading ? t("status.connecting") : statusLabel(t, health.data?.status)}</strong>
            </div>
            <div className="status-chip good">
              <span className="pulse-dot green" />
              {t("status.db")}: <strong>{statusLabel(t, health.data?.database?.status, "connected")}</strong>
            </div>
            <div className={`status-chip ${freshnessText === "STALE" ? "warn" : "good"}`}>
              <span className={`pulse-dot ${freshnessText === "STALE" ? "amber" : "green"}`} />
              {t("status.feed")}: <strong>{statusLabel(t, freshnessText, "nominal")}</strong>
            </div>
          </div>
          <LanguageSwitcher />
        </div>
      </header>

      {/* Main Grid Section */}
      <div className="terminal-main-grid">
        {/* Top Section: Price Hero & Chart (Left) + AI Directional Bias (Right) */}
        <div className="terminal-top-row">
          {/* Left: Hero Ticker & Professional Chart */}
          <div className="t-panel">
            <div className="t-panel-header">
              <div className="t-panel-title">
                <span className="accent-bar" />
                <span>{t("market.execution_title")}</span>
              </div>
              <div className="t-panel-actions">
                <span>{t("market.timeframe")}</span>
                <span>&bull;</span>
                <span>{t("market.spot_feed")}</span>
              </div>
            </div>
            <div className="t-panel-body" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <MarketCard
                item={selectedMarket || { symbol: "XAUUSD", price: null }}
                liveTick={liveTick}
                wsStatus={wsStatus}
              />
              <PanelContent title={t("panels.price_chart")} state={detail} empty={!candles.length}>
                <PriceChart candles={candles} symbol={asset} />
              </PanelContent>
            </div>
          </div>

          {/* Right: AI Prediction & Bias Card */}
          <div className="t-panel">
            <div className="t-panel-header">
              <div className="t-panel-title">
                <span className="accent-bar" />
                <span>{t("prediction.ai_forecast_title")}</span>
              </div>
              <div className="t-panel-actions">
                <span>{t("prediction.inference_engine")}</span>
              </div>
            </div>
            <div className="t-panel-body">
              {(prediction.loading || (!prediction.data && !prediction.error)) ? (
                <StatusPanel title={t("panels.ai_prediction")} message={t("status_panel.loading_telemetry")} />
              ) : prediction.error && !prediction.data ? (
                <StatusPanel title={t("panels.ai_prediction")} message={prediction.error.message || t("status_panel.unavailable")} type="error" />
              ) : (
                <PredictionCard
                  predictionDaily={prediction.data || null}
                  predictionWeekly={predictionWeekly.data || null}
                  latestCandle={candles[candles.length - 1]}
                  horizon={predictionHorizon}
                  onHorizonChange={setPredictionHorizon}
                />
              )}
            </div>
          </div>
        </div>

        {/* Middle Section: Technical Analysis, Probabilistic Scenarios, AI Explanation */}
        <div className="terminal-middle-row">
          {/* Technical Analysis */}
          <div className="t-panel">
            <div className="t-panel-header">
              <div className="t-panel-title">
                <span className="accent-bar" />
                <span>{t("technicals.title")}</span>
              </div>
              <div className="t-panel-actions">
                <span>{t("technicals.indicators_subtitle")}</span>
              </div>
            </div>
            <div className="t-panel-body">
              <PanelContent title={t("panels.technicals")} state={detail} empty={!candles.length}>
                <TechnicalPanel candles={candles} symbol={asset} />
              </PanelContent>
            </div>
          </div>

          {/* Probabilistic Scenarios */}
          <div className="t-panel">
            <div className="t-panel-header">
              <div className="t-panel-title">
                <span className="accent-bar" />
                <span>{t("scenarios.title")}</span>
                <span
                  style={{
                    fontSize: "10px",
                    padding: "2px 7px",
                    borderRadius: "4px",
                    background: "rgba(212, 175, 55, 0.15)",
                    color: "var(--gold-accent)",
                    fontWeight: "700",
                    marginLeft: "8px",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  {predictionHorizon === "weekly"
                    ? (t("prediction.toggle_weekly") || "Weekly")
                    : (t("prediction.toggle_daily") || "Daily")}
                </span>
              </div>
              <div className="t-panel-actions">
                <span>
                  {predictionHorizon === "weekly"
                    ? "H1 → 120H"
                    : (t("scenarios.subtitle") || "H1 → 24H")}
                </span>
              </div>
            </div>
            <div className="t-panel-body">
              <PanelContent
                title={t("panels.scenarios")}
                state={predictionHorizon === "weekly" ? predictionWeekly : prediction}
                empty={!(predictionHorizon === "weekly" ? predictionWeekly.data?.scenarios : prediction.data?.scenarios)?.length}
              >
                <ScenarioPanel
                  scenarios={
                    (predictionHorizon === "weekly"
                      ? predictionWeekly.data?.scenarios
                      : prediction.data?.scenarios) || []
                  }
                />
              </PanelContent>
            </div>
          </div>
        </div>
      </div>

    </main>
  );
}

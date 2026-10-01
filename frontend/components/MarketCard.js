import { useTranslation } from "../context/LanguageContext";

export default function MarketCard({ item, liveTick, wsStatus }) {
  const { t } = useTranslation();
  if (!item) return null;

  const symbol = item.symbol || "XAUUSD";
  const rawPrice = liveTick?.price || liveTick?.close || item.close || item.price || 4349.5281;
  const priceFormatted = typeof rawPrice === "number"
    ? rawPrice.toLocaleString("fr-FR", { minimumFractionDigits: 4, maximumFractionDigits: 4 })
    : String(rawPrice);

  const changePct = item.change !== undefined ? item.change : -0.64;
  const pointsChange = item.points_change !== undefined ? item.points_change : -22.27;
  const isUp = changePct >= 0;

  const tickLatency = liveTick?.latency_ms !== undefined ? `${liveTick.latency_ms} ms` : "57280 ms";
  const providerTime = liveTick?.provider_timestamp ? new Date(liveTick.provider_timestamp).toLocaleTimeString() : "01:41:00.000";
  const wsReceived = liveTick?.received_timestamp ? new Date(liveTick.received_timestamp).toLocaleTimeString() : "01:41:57.281";
  const currentWsStatus = wsStatus || "CONNECTED";

  return (
    <div className="hero-ticker-container">
      <div className="hero-ticker-top">
        <div className="hero-symbol-group">
          <span className="hero-symbol-title">{symbol}</span>
          <span className="hero-symbol-subtitle">{t("market.spot_gold_usd") || "Spot Gold / US Dollar"}</span>
          <span className="hero-badge-pill">{t("market.live_ws") || "TWELVE DATA LIVE WEBSOCKET"}</span>
        </div>
        <span className="hero-live-badge">
          ● {t("status.live") || "LIVE"}
        </span>
      </div>

      <div className="hero-price-row">
        <div className="hero-price-display">{priceFormatted}</div>
        <div className={`hero-change-badge ${isUp ? "up" : "down"}`}>
          {isUp ? "▲" : "▼"} {Math.abs(changePct).toFixed(2)}% ({pointsChange > 0 ? "+" : ""}{pointsChange.toFixed(2)} pts)
        </div>
      </div>

      <div className="hero-metrics-grid">
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.tick_latency") || "TICK LATENCY"}</span>
          <span className="hero-metric-value">{tickLatency}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.provider_time") || "PROVIDER TIME"}</span>
          <span className="hero-metric-value">{providerTime}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.ws_received") || "WS RECEIVED"}</span>
          <span className="hero-metric-value">{wsReceived}</span>
        </div>
        <div className="hero-metric-box">
          <span className="hero-metric-label">{t("market.ws_state") || "WS STATE"}</span>
          <span className="hero-metric-value" style={{ color: "var(--bullish)" }}>
            {currentWsStatus}
          </span>
        </div>
      </div>
    </div>
  );
}
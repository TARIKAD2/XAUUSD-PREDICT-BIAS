import { useTranslation } from "../context/LanguageContext";

function last(values) {
  return values.length ? values[values.length - 1] : null;
}

function sma(values, period) {
  if (values.length < period) return null;
  const slice = values.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

function rsi(closes, period = 14) {
  if (closes.length <= period) return null;
  let gains = 0;
  let losses = 0;
  for (let i = closes.length - period; i < closes.length; i += 1) {
    const change = closes[i] - closes[i - 1];
    if (change >= 0) gains += change;
    else losses -= change;
  }
  if (losses === 0) return 100;
  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

function ema(values, period) {
  if (values.length < period) return null;
  const k = 2 / (period + 1);
  let current = sma(values.slice(0, period), period);
  for (let i = period; i < values.length; i += 1) {
    current = values[i] * k + current * (1 - k);
  }
  return current;
}

export default function TechnicalPanel({ candles = [], symbol = "XAUUSD" }) {
  const { t } = useTranslation();
  const closes = (candles || []).map((c) => Number(c.close)).filter((v) => Number.isFinite(v));
  const highs = (candles || []).map((c) => Number(c.high)).filter((v) => Number.isFinite(v));
  const lows = (candles || []).map((c) => Number(c.low)).filter((v) => Number.isFinite(v));

  if (closes.length < 14) {
    return <div className="t-status-box">{t("technicals.insufficient_candles")}</div>;
  }

  const currentPrice = last(closes);
  const rsiValue = rsi(closes);
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const macd = ema12 != null && ema26 != null ? ema12 - ema26 : null;
  const atr = highs.length === lows.length && highs.length >= 14
    ? sma(highs.map((h, i) => h - lows[i]), 14)
    : null;
  const sma200 = sma(closes, Math.min(200, closes.length));
  const ema200 = ema(closes, 200);

  const isAboveSMA = sma200 != null && currentPrice != null ? currentPrice >= sma200 : null;
  const smaDiff = sma200 != null && currentPrice != null ? currentPrice - sma200 : null;
  const isAboveEMA = ema200 != null && currentPrice != null ? currentPrice >= ema200 : null;
  const emaDiff = ema200 != null && currentPrice != null ? currentPrice - ema200 : null;

  // RSI styling
  const rsiPct = rsiValue != null ? Math.min(100, Math.max(0, rsiValue)) : 50;
  const rsiColor = rsiValue > 70 ? "var(--bearish)" : rsiValue < 30 ? "var(--bullish)" : "var(--gold-accent)";

  return (
    <div className="technicals-grid">
      {/* 200 SMA Trend */}
      <div className="tech-indicator-card">
        <div className="tech-indicator-left">
          <span className="tech-name">{t("technicals.sma_filter")}</span>
          <span className="tech-desc">
            {sma200 != null
              ? `${t("technicals.level")}: ${sma200.toFixed(2)} (${smaDiff >= 0 ? "+" : ""}${smaDiff.toFixed(2)})`
              : t("technicals.calculating_baseline")}
          </span>
        </div>
        <span className={`tech-value ${isAboveSMA ? "bullish" : isAboveSMA === false ? "bearish" : "neutral"}`}>
          {isAboveSMA ? t("technicals.above_sma") : isAboveSMA === false ? t("technicals.below_sma") : t("common.not_available")}
        </span>
      </div>

      {/* 200 EMA Trend */}
      <div className="tech-indicator-card">
        <div className="tech-indicator-left">
          <span className="tech-name">{t("technicals.ema_filter")}</span>
          <span className="tech-desc">
            {ema200 != null
              ? `${t("technicals.level")}: ${ema200.toFixed(2)} (${emaDiff >= 0 ? "+" : ""}${emaDiff.toFixed(2)})`
              : t("technicals.calculating_baseline")}
          </span>
        </div>
        <span className={`tech-value ${isAboveEMA ? "bullish" : isAboveEMA === false ? "bearish" : "neutral"}`}>
          {isAboveEMA ? t("technicals.above_ema") : isAboveEMA === false ? t("technicals.below_ema") : t("common.not_available")}
        </span>
      </div>

      {/* RSI */}
      <div className="tech-indicator-card">
        <div className="tech-indicator-left">
          <span className="tech-name">{t("technicals.rsi_momentum")}</span>
          <span className="tech-desc">
            {rsiValue != null
              ? rsiValue > 70
                ? t("technicals.overbought")
                : rsiValue < 30
                ? t("technicals.oversold")
                : t("technicals.neutral_eq")
              : t("technicals.awaiting_calc")}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div className="rsi-meter-wrap">
            <div className="rsi-meter-bar">
              <div
                className="rsi-meter-fill"
                style={{ width: `${rsiPct}%`, backgroundColor: rsiColor }}
              />
            </div>
          </div>
          <span className="tech-value font-mono">
            {rsiValue != null ? rsiValue.toFixed(2) : t("common.not_available")}
          </span>
        </div>
      </div>

      {/* MACD */}
      <div className="tech-indicator-card">
        <div className="tech-indicator-left">
          <span className="tech-name">{t("technicals.macd_oscillator")}</span>
          <span className="tech-desc">{t("technicals.macd_desc")}</span>
        </div>
        <span className={`tech-value ${macd != null && macd >= 0 ? "bullish" : "bearish"}`}>
          {macd != null ? (macd >= 0 ? `+${macd.toFixed(4)}` : macd.toFixed(4)) : t("common.not_available")}
        </span>
      </div>

      {/* ATR */}
      <div className="tech-indicator-card">
        <div className="tech-indicator-left">
          <span className="tech-name">{t("technicals.atr_volatility")}</span>
          <span className="tech-desc">{t("technicals.atr_desc")}</span>
        </div>
        <span className="tech-value font-mono">
          {atr != null ? `${atr.toFixed(2)} ${t("market.pts")}` : t("common.not_available")}
        </span>
      </div>

      {/* Institutional Market Structure */}
      {symbol === "XAUUSD" && (
        <div className="tech-indicator-card">
          <div className="tech-indicator-left">
            <span className="tech-name">{t("technicals.market_structure")}</span>
            <span className="tech-desc">{t("technicals.market_struct_desc")}</span>
          </div>
          <span className="tech-value neutral" style={{ fontSize: "11px" }}>
            {t("technicals.model_embedded")}
          </span>
        </div>
      )}
    </div>
  );
}

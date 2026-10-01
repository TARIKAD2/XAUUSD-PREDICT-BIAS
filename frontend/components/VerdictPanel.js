import { useTranslation } from "../context/LanguageContext";

export default function VerdictPanel({ verdict }) {
  const { t } = useTranslation();
  if (!verdict) return null;

  const bias = (verdict.bias || "NEUTRAL").toUpperCase();
  const biasClass = bias.includes("BULL")
    ? "bullish"
    : bias.includes("BEAR")
    ? "bearish"
    : "neutral";

  return (
    <div className="verdict-panel">
      <div className="section-mini-header">
        <span className="accent-bar" />
        <span>{t("war_room.verdict_title")}</span>
      </div>

      <div className="verdict-body-grid">
        <div className="verdict-summary-card">
          <div className="verdict-top-row">
            <div>
              <div className="v-label">{t("war_room.dominant_scenario")}</div>
              <div className="v-dominant-title font-mono">{verdict.dominant_scenario}</div>
            </div>
            <div>
              <div className="v-label">{t("war_room.pre_event_bias")}</div>
              <span className={`signal-badge ${biasClass}`} style={{ fontSize: "12px", padding: "4px 10px" }}>
                {bias.includes("BULL") ? t("prediction.bullish") : bias.includes("BEAR") ? t("prediction.bearish") : t("prediction.neutral")}
              </span>
            </div>
          </div>

          <div className="v-drivers-section">
            <span className="v-label">{t("war_room.primary_drivers")}</span>
            <ul className="v-drivers-list">
              {(verdict.main_drivers || []).map((d, i) => (
                <li key={i}>
                  <span className="driver-bullet">▸</span>
                  <span>{d}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="verdict-risk-card">
          <div className="risk-item">
            <span className="v-label" style={{ color: "var(--warning)" }}>{t("war_room.liquidity_risk")}</span>
            <p className="risk-text">{verdict.main_risk}</p>
          </div>

          <div className="risk-item" style={{ marginTop: "10px" }}>
            <span className="v-label" style={{ color: "var(--bearish)" }}>{t("war_room.model_invalidation")}</span>
            <p className="risk-text font-mono" style={{ color: "var(--text-secondary)" }}>
              {verdict.invalidation_condition}
            </p>
          </div>
        </div>
      </div>

      <div className="verdict-disclaimer">
        <strong>{t("war_room.notice")}:</strong> {verdict.disclaimer}
      </div>
    </div>
  );
}

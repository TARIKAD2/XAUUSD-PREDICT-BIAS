import { useTranslation } from "../context/LanguageContext";

export default function ScenarioCards({ scenarios = [] }) {
  const { t } = useTranslation();
  if (!scenarios?.length) {
    return <div className="t-status-box">{t("additional.no_event_scenarios")}</div>;
  }

  return (
    <div className="war-room-scenarios-panel">
      <div className="section-mini-header">
        <span className="accent-bar" />
        <span>{t("war_room.contingency_title")}</span>
      </div>

      <div className="scenarios-three-grid">
        {scenarios.map((sc, idx) => {
          const dir = (sc.expected_direction || "NEUTRAL").toUpperCase();
          const cardClass = dir.includes("BULL")
            ? "bullish"
            : dir.includes("BEAR")
            ? "bearish"
            : "neutral";

          return (
            <div className={`war-scenario-card ${cardClass}`} key={`${sc.name}-${idx}`}>
              <div className="sc-header">
                <div>
                  <span className="sc-name">{sc.name}</span>
                  <div className="sc-prob font-mono">{sc.probability.toFixed(1)}% {t("additional.probability")}</div>
                </div>
                <span className={`signal-badge ${cardClass}`}>
                  {dir.includes("BULL") ? t("prediction.bullish") : dir.includes("BEAR") ? t("prediction.bearish") : t("prediction.neutral")}
                </span>
              </div>

              <div className="sc-target-box">
                <span className="sc-target-label">{t("war_room.target_range")}</span>
                <span className="sc-target-val font-mono">{sc.target_range}</span>
              </div>

              <div className="sc-section">
                <span className="sc-label">{t("war_room.core_assumptions")}</span>
                <p className="sc-text">{sc.assumptions}</p>
              </div>

              <div className="sc-section">
                <span className="sc-label" style={{ color: "var(--bearish)" }}>{t("war_room.invalidation_threshold")}</span>
                <p className="sc-text font-mono" style={{ color: "var(--text-secondary)" }}>{sc.invalidation}</p>
              </div>

              <div className="sc-section" style={{ borderBottom: "none", paddingBottom: "0" }}>
                <span className="sc-label" style={{ color: "var(--warning)" }}>{t("war_room.execution_risk")}</span>
                <p className="sc-text text-muted">{sc.risk_note}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

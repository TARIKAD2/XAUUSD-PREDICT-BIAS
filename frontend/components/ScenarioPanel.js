import { useTranslation } from "../context/LanguageContext";

export default function ScenarioPanel({ scenarios = [] }) {
  const { t } = useTranslation();
  if (!scenarios?.length) {
    return <div className="t-status-box">{t("scenarios.no_scenarios")}</div>;
  }

  return (
    <div className="technicals-grid">
      {scenarios.map((item, idx) => {
        const dir = (item.expected_direction || "").toLowerCase();
        const dirClass = dir.includes("bull")
          ? "bullish"
          : dir.includes("bear")
          ? "bearish"
          : "neutral";

        const dirLabel = dir.includes("bull")
          ? t("prediction.bullish")
          : dir.includes("bear")
          ? t("prediction.bearish")
          : t("prediction.neutral");

        return (
          <div className="tech-indicator-card" key={item.name || idx}>
            {/* Left: scenario name + details */}
            <div className="tech-indicator-left">
              <span className="tech-name">{item.name}</span>
              <span className="tech-desc">
                {t("scenarios.trigger_cond")}: {item.condition || t("scenarios.baseline")}
              </span>
              {item.invalidation && (
                <span className="tech-desc" style={{ color: "var(--bearish)", fontFamily: "var(--font-mono)" }}>
                  {t("scenarios.invalidation")}: {item.invalidation}
                </span>
              )}
              {item.context && (
                <span className="tech-desc" style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
                  {item.context}
                </span>
              )}
            </div>

            {/* Right: directional badge */}
            <span className={`tech-value ${dirClass}`}>
              {dirLabel}
            </span>
          </div>
        );
      })}
    </div>
  );
}

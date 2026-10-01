import { useTranslation } from "../context/LanguageContext";

function formatVal(val, unit = "", pendingLabel = "Pending") {
  if (val === null || val === undefined || val === "") return pendingLabel;
  const num = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(num)) return String(val);
  return `${num > 0 && unit === "%" ? "+" : ""}${num.toFixed(1)}${unit}`;
}

export default function ExpectedMetrics({ metrics = [] }) {
  const { t } = useTranslation();
  if (!metrics?.length) {
    return <div className="t-status-box">{t("additional.no_consensus_metrics")}</div>;
  }

  return (
    <div className="expected-metrics-panel">
      <div className="section-mini-header">
        <span className="accent-bar" />
        <span>{t("war_room.consensus_metrics_title")}</span>
      </div>

      <div className="metrics-grid">
        {metrics.map((m, idx) => {
          const unit = m.unit || "";
          return (
            <div className="metric-box-card" key={`${m.name}-${idx}`}>
              <div className="metric-box-title">{m.name}</div>
              <div className="metric-comparison-row">
                <div className="metric-field forecast">
                  <span className="label">{t("war_room.estimate")}</span>
                  <span className="value font-mono">{formatVal(m.forecast, unit, t("war_room.pending"))}</span>
                </div>
                <div className="metric-field previous">
                  <span className="label">{t("war_room.previous_metric")}</span>
                  <span className="value font-mono">{formatVal(m.previous, unit, t("war_room.pending"))}</span>
                </div>
                <div className={`metric-field actual ${m.actual !== null && m.actual !== undefined ? "published" : ""}`}>
                  <span className="label">{t("war_room.actual_metric")}</span>
                  <span className="value font-mono">{formatVal(m.actual, unit, t("war_room.pending"))}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

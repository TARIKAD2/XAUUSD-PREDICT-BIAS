import { useTranslation } from "../context/LanguageContext";

export default function SignalMatrix({ factors = [] }) {
  const { t } = useTranslation();
  if (!factors?.length) {
    return <div className="t-status-box">{t("additional.no_signal_matrix")}</div>;
  }

  return (
    <div className="signal-matrix-panel">
      <div className="section-mini-header">
        <span className="accent-bar" />
        <span>{t("war_room.matrix_title")}</span>
      </div>

      <div className="terminal-table-wrapper">
        <table className="terminal-table">
          <thead>
            <tr>
              <th style={{ width: "25%" }}>{t("war_room.col_factor")}</th>
              <th style={{ width: "15%" }}>{t("war_room.col_bias")}</th>
              <th style={{ width: "15%" }}>{t("war_room.col_reading")}</th>
              <th style={{ width: "45%" }}>{t("war_room.col_rationale")}</th>
            </tr>
          </thead>
          <tbody>
            {factors.map((f, idx) => {
              const status = (f.status || "NEUTRAL").toUpperCase();
              const badgeClass = status.includes("BULL")
                ? "bullish"
                : status.includes("BEAR")
                ? "bearish"
                : "neutral";

              return (
                <tr key={`${f.factor}-${idx}`}>
                  <td className="primary-cell">{f.factor}</td>
                  <td>
                    <span className={`signal-badge ${badgeClass}`}>
                      {status === "BULLISH" ? `▲ ${t("prediction.bullish")}` : status === "BEARISH" ? `▼ ${t("prediction.bearish")}` : `■ ${t("prediction.neutral")}`}
                    </span>
                  </td>
                  <td className="font-mono text-muted">
                    {f.indicator_value || "---"}
                  </td>
                  <td style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                    {f.reason}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useTranslation } from "../context/LanguageContext";

export default function QualityPanel({ data }) {
  const { t } = useTranslation();
  const items = data?.items || [];
  if (!items.length) {
    return <div className="t-status-box">{t("quality.no_audit")}</div>;
  }

  return (
    <div className="terminal-table-wrapper">
      <table className="terminal-table">
        <thead>
          <tr>
            <th>{t("quality.symbol")}</th>
            <th>{t("quality.provider")}</th>
            <th>{t("quality.candles_count")}</th>
            <th>{t("quality.detected_gaps")}</th>
            <th>{t("quality.invalid_ohlc")}</th>
            <th>{t("quality.staleness_flag")}</th>
            <th>{t("quality.last_ingestion")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={`${row.symbol}-${row.timeframe}`}>
              <td className="primary-cell">{row.symbol} ({row.timeframe || "1h"})</td>
              <td>{row.provider_status || t("additional.default_provider")}</td>
              <td>{row.candle_count}</td>
              <td className={row.gap_count > 0 ? "warn" : "good"}>{row.gap_count}</td>
              <td className={row.invalid_ohlc > 0 ? "bad" : "good"}>{row.invalid_ohlc}</td>
              <td>
                <span className={`status-chip ${row.stale ? "warn" : "good"}`}>
                  <strong>{row.stale ? t("status.stale") : t("status.fresh")}</strong>
                </span>
              </td>
              <td className="text-muted">
                {row.last_timestamp ? new Date(row.last_timestamp).toLocaleString() : t("common.not_available")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

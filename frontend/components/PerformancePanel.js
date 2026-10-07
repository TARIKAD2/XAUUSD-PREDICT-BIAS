import { useTranslation } from "../context/LanguageContext";
import { formatDate } from "../services/dateFormat";

function metricValue(metrics, name) {
  const found = (metrics || []).find((m) => m.name === name);
  return found ? Number(found.value).toFixed(4) : "---";
}

function metricPercent(metrics, name) {
  const value = metricValue(metrics, name);
  return value !== "---" ? `${(Number(value) * 100).toFixed(1)}%` : "---";
}

export default function PerformancePanel({ data }) {
  const { t } = useTranslation();
  const items = data?.items || [];
  if (!items.length) {
    return <div className="t-status-box">{t("performance.no_metrics")}</div>;
  }

  return (
    <div>
      <div className="text-muted" style={{ marginBottom: "12px" }}>
        <strong>{t("performance.oos_title")}</strong> - {t("performance.oos_description")}
      </div>
      <div className="terminal-table-wrapper">
        <table className="terminal-table">
          <thead>
            <tr>
              <th>{t("performance.symbol")}</th>
              <th>{t("performance.architecture")}</th>
              <th>{t("performance.accuracy")}</th>
              <th>{t("performance.precision")}</th>
              <th>{t("performance.recall")}</th>
              <th>{t("performance.f1")}</th>
              <th>{t("performance.roc_auc")}</th>
              <th>{t("performance.log_loss")}</th>
              <th>{t("performance.brier")}</th>
              <th>{t("performance.testing_period")}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row, index) => {
              const acc = metricValue(row.metrics, "accuracy");
              const f1 = metricValue(row.metrics, "f1");
              return (
                <tr key={`${row.symbol}-${row.model_version}-${index}`}>
                  <td className="primary-cell">{row.symbol}</td>
                  <td>{row.model_version}</td>
                  <td className={acc !== "---" && Number(acc) > 0.55 ? "good" : ""}>
                    {acc !== "---" ? `${(Number(acc) * 100).toFixed(1)}%` : "---"}
                  </td>
                  <td>{metricPercent(row.metrics, "precision")}</td>
                  <td>{metricPercent(row.metrics, "recall")}</td>
                  <td className={f1 !== "---" && Number(f1) > 0.55 ? "good" : ""}>
                    {f1 !== "---" ? `${(Number(f1) * 100).toFixed(1)}%` : "---"}
                  </td>
                  <td>
                    {metricPercent(row.metrics, "roc_auc") !== "---"
                      ? metricPercent(row.metrics, "roc_auc")
                      : metricPercent(row.metrics, "roc_auc_ovr_weighted")}
                  </td>
                  <td>{metricValue(row.metrics, "log_loss")}</td>
                  <td>{metricValue(row.metrics, "brier")}</td>
                  <td className="text-muted">
                    {row.testing_period_start
                      ? `${formatDate(row.testing_period_start)} → ${formatDate(row.testing_period_end)}`
                      : t("common.not_available")}
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

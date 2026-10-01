import { useTranslation } from "../context/LanguageContext";

export default function ProbabilityGauge({ probabilities }) {
  const { t } = useTranslation();
  if (!probabilities) return null;

  const cool = Number(probabilities.cool_pct || 0);
  const inline = Number(probabilities.inline_pct || 0);
  const hot = Number(probabilities.hot_pct || 0);

  return (
    <div className="prob-gauge-panel">
      <div className="gauge-header">
        <span className="gauge-title">{t("war_room.dist_title")}</span>
        <span className="gauge-sub font-mono">{t("war_room.consensus_model")}</span>
      </div>

      <div className="gauge-cards-grid">
        <div className="gauge-outcome-card cool">
          <div className="outcome-name">{t("war_room.cool_soft")}</div>
          <div className="outcome-pct font-mono">{cool.toFixed(1)}%</div>
          <div className="outcome-desc">{t("war_room.cool_desc")}</div>
        </div>

        <div className="gauge-outcome-card inline">
          <div className="outcome-name">{t("war_room.in_line")}</div>
          <div className="outcome-pct font-mono">{inline.toFixed(1)}%</div>
          <div className="outcome-desc">{t("war_room.in_line_desc")}</div>
        </div>

        <div className="gauge-outcome-card hot">
          <div className="outcome-name">{t("war_room.hot_high")}</div>
          <div className="outcome-pct font-mono">{hot.toFixed(1)}%</div>
          <div className="outcome-desc">{t("war_room.hot_desc")}</div>
        </div>
      </div>

      <div className="gauge-bar-track">
        <div className="gauge-segment cool" style={{ width: `${cool}%` }} title={`${t("war_room.cool_soft")}: ${cool}%`} />
        <div className="gauge-segment inline" style={{ width: `${inline}%` }} title={`${t("war_room.in_line")}: ${inline}%`} />
        <div className="gauge-segment hot" style={{ width: `${hot}%` }} title={`${t("war_room.hot_high")}: ${hot}%`} />
      </div>

      {probabilities.rationale && (
        <div className="gauge-rationale">
          <span className="k">{t("war_room.methodology")}:</span> {probabilities.rationale}
        </div>
      )}
    </div>
  );
}

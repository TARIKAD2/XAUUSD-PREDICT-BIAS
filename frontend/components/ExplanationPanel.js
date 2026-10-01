import { useTranslation } from "../context/LanguageContext";

export default function ExplanationPanel({ prediction, explanation }) {
  const { t } = useTranslation();
  const features = explanation?.top_features || prediction?.top_features || [];
  const mainContext = explanation?.note || prediction?.market_context || t("explanation.default_context");
  const reasons = prediction?.reasons || [];

  return (
    <div className="explanation-content">
      <div className="explanation-context-box">
        {mainContext}
      </div>

      {reasons.length > 0 && (
        <div className="explanation-reasons-list">
          {reasons.map((reason, idx) => (
            <div className="explanation-reason-item" key={idx}>
              <span className="reason-bullet">▸</span>
              <span>{reason}</span>
            </div>
          ))}
        </div>
      )}

      {features.length > 0 && (
        <div className="features-container" style={{ marginTop: "4px" }}>
          <div className="features-title">{t("explanation.weight_title")}</div>
          <div className="features-list">
            {features.slice(0, 4).map((item) => (
              <div className="feature-row" key={item.feature}>
                <span className="feature-name">{item.feature}</span>
                <span className={`feature-value ${Number(item.contribution) >= 0 ? "pos" : "neg"}`}>
                  {Number(item.contribution) >= 0 ? "+" : ""}
                  {Number(item.contribution).toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

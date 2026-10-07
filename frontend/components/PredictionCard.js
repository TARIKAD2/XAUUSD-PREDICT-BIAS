"use client";
import { useState } from "react";
import { useTranslation } from "../context/LanguageContext";
import { formatDateTime } from "../services/dateFormat";

/**
 * PredictionCard – Daily / Weekly toggle.
 *
 * Props:
 *   predictionDaily   – API response for ?horizon=daily
 *   predictionWeekly  – API response for ?horizon=weekly  (may be null / error state)
 *   latestCandle      – most recent closed H1 candle from the market endpoint
 *   horizon           – active horizon mode ("daily" | "weekly")
 *   onHorizonChange   – callback invoked when user toggles horizon
 */
export default function PredictionCard({
  predictionDaily,
  predictionWeekly,
  latestCandle,
  horizon = "daily",
  onHorizonChange,
}) {
  const { t } = useTranslation();
  const [internalMode, setInternalMode] = useState("daily");

  const mode = onHorizonChange ? horizon : internalMode;
  const setMode = (nextMode) => {
    if (onHorizonChange) {
      onHorizonChange(nextMode);
    } else {
      setInternalMode(nextMode);
    }
  };

  const prediction = mode === "weekly" ? predictionWeekly : predictionDaily;

  if (!predictionDaily && !predictionWeekly) return null;

  const direction = (prediction?.direction || "").toUpperCase();
  const confidence =
    prediction?.confidence !== undefined
      ? (prediction.confidence * 100).toFixed(1)
      : null;
  const probabilities = prediction?.probabilities || null;
  const bullPct = probabilities ? (probabilities.bullish * 100).toFixed(1) : null;
  const bearPct = probabilities ? (probabilities.bearish * 100).toFixed(1) : null;

  // Horizon from API field, never hardcoded
  const horizonHours = prediction?.horizon_hours ?? (mode === "weekly" ? 120 : 24);
  const horizonLabel =
    mode === "weekly"
      ? t("prediction.horizon_val_weekly") || "120H Forward (Weekly Bias)"
      : t("prediction.horizon_val_daily") || "24H Forward (Daily Bias)";

  const factors = prediction?.top_features?.length ? prediction.top_features : [];
  const factorsTitle = t("prediction.top_factors") || "Top Contributing Factors";
  const factorsTitleWithoutShap = factorsTitle.replace(/\s*\(SHAP\)\s*$/i, "");

  const predictionTimeRaw =
    prediction?.prediction_timestamp_utc ||
    prediction?.timestamp ||
    prediction?.prediction_as_of;
  const candleTimeRaw =
    prediction?.model_input_timestamp ||
    prediction?.market_as_of_utc ||
    prediction?.data_timestamp ||
    latestCandle?.timestamp;

  const predictionTimeFormatted = formatDateTime(predictionTimeRaw, { timeZone: "UTC", second: "2-digit" });
  const candleTimeFormatted = formatDateTime(candleTimeRaw, { timeZone: "UTC" });

  // Error/unavailable for the selected mode
  const isUnavailable = !prediction;
  const weeklyUnavailable = mode === "weekly" && !predictionWeekly;

  return (
    <div className="forecast-card-body">
      {/* Daily | Weekly Toggle */}
      <div className="horizon-toggle-row">
        <button
          id="toggle-daily"
          className={`horizon-toggle-btn${mode === "daily" ? " active" : ""}`}
          onClick={() => setMode("daily")}
          aria-pressed={mode === "daily"}
        >
          {t("prediction.toggle_daily") || "Daily"}
          <span className="horizon-toggle-sub">H1 → 24H</span>
        </button>
        <button
          id="toggle-weekly"
          className={`horizon-toggle-btn${mode === "weekly" ? " active" : ""}`}
          onClick={() => setMode("weekly")}
          aria-pressed={mode === "weekly"}
        >
          {t("prediction.toggle_weekly") || "Weekly"}
          <span className="horizon-toggle-sub">H1 → 120H</span>
        </button>
      </div>

      {/* Unavailable state for weekly */}
      {weeklyUnavailable ? (
        <div className="prediction-unavailable">
          <span className="unavail-icon">⚠</span>
          <span>{t("prediction.weekly_unavailable") || "Weekly model not available."}</span>
        </div>
      ) : isUnavailable ? (
        <div className="prediction-unavailable">
          <span className="unavail-icon">⚠</span>
          <span>{t("prediction.no_prediction") || "No prediction model output available."}</span>
        </div>
      ) : (
        <>
          {/* Directional Bias Banner */}
          <div className={`bias-banner ${direction.toLowerCase()}`}>
            <div className="bias-left">
              <span className="bias-label">
                {t("prediction.model_dir_bias") || "MODEL DIRECTIONAL BIAS"}
              </span>
              <span className={`bias-value ${direction.toLowerCase()}`}>{direction}</span>
            </div>
            <div className="bias-confidence-box">
              {confidence !== null
                ? `${t("prediction.confidence") || "CONFIDENCE"}: ${confidence}%`
                : t("prediction.confidence") || "CONFIDENCE"}
            </div>
          </div>

          {/* Probability Bar */}
          {probabilities && (
            <div className="prob-bar-wrapper">
              <div className="prob-bar-container">
                <div className="prob-seg bullish" style={{ width: `${bullPct}%` }} />
                {probabilities.neutral ? (
                  <div
                    className="prob-seg neutral"
                    style={{ width: `${(probabilities.neutral * 100).toFixed(1)}%` }}
                  />
                ) : null}
                <div className="prob-seg bearish" style={{ width: `${bearPct}%` }} />
              </div>
              <div className="prob-labels">
                <span className="bull">
                  ▲ {t("prediction.bullish") || "BULLISH"} {bullPct}%
                </span>
                <span className="bear">
                  ▼ {t("prediction.bearish") || "BEARISH"} {bearPct}%
                </span>
              </div>
            </div>
          )}

          {/* Model Contributing Factors */}
          {factors.length > 0 && (
            <div className="shap-factors-section">
              <span className="shap-title">
                {prediction?.explanation_method?.toLowerCase() === "shap" ? factorsTitle : factorsTitleWithoutShap}
              </span>
              <div className="shap-list">
                {factors.map((f, i) => (
                  <div className="shap-row" key={f.feature || i}>
                    <span className="shap-feature">{f.feature}</span>
                    <span className={`shap-value ${f.contribution >= 0 ? "pos" : "neg"}`}>
                      {f.contribution >= 0 ? "+" : ""}
                      {f.contribution.toFixed(4)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Model Timing & Horizon Telemetry */}
          <div className="model-meta-footer">
            <div className="model-meta-row">
              <span>{t("prediction.horizon") || "Prediction Horizon"}:</span>
              <strong className="num-ltr">{horizonLabel}</strong>
            </div>
            <div className="model-meta-row">
              <span>{t("prediction.last_candle_time") || "Last Input Candle"}:</span>
              <strong className="num-ltr">{candleTimeFormatted}</strong>
            </div>
            <div className="model-meta-row">
              <span>{t("prediction.last_prediction_time") || "Last ML Prediction"}:</span>
              <strong className="num-ltr">{predictionTimeFormatted}</strong>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
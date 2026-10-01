"use client";
import { useState, useMemo } from "react";
import { useTranslation } from "../context/LanguageContext";

// Rolling SMA calculation
function calculateRollingSMA(candles, period = 200) {
  const result = new Array(candles.length).fill(null);
  let sum = 0;
  for (let i = 0; i < candles.length; i++) {
    const val = Number(candles[i].close);
    sum += val;
    if (i >= period) {
      sum -= Number(candles[i - period].close);
      result[i] = sum / period;
    } else if (i === period - 1) {
      result[i] = sum / period;
    } else {
      // For history shorter than period, provide rolling SMA if at least 10 bars
      if (i >= 9) {
        result[i] = sum / (i + 1);
      }
    }
  }
  return result;
}

export default function PriceChart({ candles = [], symbol = "XAUUSD" }) {
  const { t } = useTranslation();
  const [hoverIndex, setHoverIndex] = useState(null);

  const {
    validCandles,
    closes,
    smaValues,
    minPrice,
    maxPrice,
    priceSpan,
    chartWidth,
    chartHeight,
    padding,
    priceLinePoints,
    areaPoints,
    smaPoints,
    yTicks,
    xTicks,
  } = useMemo(() => {
    const width = 860;
    const height = 260;
    const pad = { top: 20, right: 75, bottom: 25, left: 15 };
    const innerWidth = width - pad.left - pad.right;
    const innerHeight = height - pad.top - pad.bottom;

    if (!candles || candles.length < 2) {
      return {
        validCandles: [],
        closes: [],
        smaValues: [],
        chartWidth: width,
        chartHeight: height,
        padding: pad,
      };
    }

    const valid = candles.filter(
      (c) => c && Number.isFinite(Number(c.close)) && Number(c.close) > 0
    );

    if (valid.length < 2) {
      return {
        validCandles: [],
        closes: [],
        smaValues: [],
        chartWidth: width,
        chartHeight: height,
        padding: pad,
      };
    }

    const cList = valid.map((c) => Number(c.close));
    const smaList = calculateRollingSMA(valid, 200);

    // Compute min and max across both price and valid SMA
    let min = Math.min(...cList);
    let max = Math.max(...cList);
    smaList.forEach((v) => {
      if (v !== null && Number.isFinite(v)) {
        if (v < min) min = v;
        if (v > max) max = v;
      }
    });

    const margin = (max - min) * 0.05 || 1;
    min -= margin;
    max += margin;
    const span = max - min || 1;

    // Build price polyline points
    const pPoints = valid
      .map((c, i) => {
        const x = pad.left + (i / (valid.length - 1)) * innerWidth;
        const y = pad.top + innerHeight - ((Number(c.close) - min) / span) * innerHeight;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

    // Build area fill polygon points
    const firstX = pad.left;
    const lastX = pad.left + innerWidth;
    const bottomY = pad.top + innerHeight;
    const aPoints = `${firstX},${bottomY} ${pPoints} ${lastX},${bottomY}`;

    // Build SMA 200 polyline points
    const sPointsArr = [];
    smaList.forEach((v, i) => {
      if (v !== null && Number.isFinite(v)) {
        const x = pad.left + (i / (valid.length - 1)) * innerWidth;
        const y = pad.top + innerHeight - ((v - min) / span) * innerHeight;
        sPointsArr.push(`${x.toFixed(1)},${y.toFixed(1)}`);
      }
    });
    const sPoints = sPointsArr.join(" ");

    // Generate 5 horizontal grid lines / Y-ticks
    const ticksCount = 5;
    const yt = [];
    for (let i = 0; i <= ticksCount; i++) {
      const pVal = min + (span * i) / ticksCount;
      const y = pad.top + innerHeight - (i / ticksCount) * innerHeight;
      yt.push({ value: pVal, y });
    }

    // Generate 5 time labels / X-ticks
    const xt = [];
    const numXTicks = Math.min(6, valid.length);
    for (let i = 0; i < numXTicks; i++) {
      const idx = Math.floor((i * (valid.length - 1)) / (numXTicks - 1));
      const c = valid[idx];
      const x = pad.left + (idx / (valid.length - 1)) * innerWidth;
      const d = c?.timestamp ? new Date(c.timestamp) : null;
      const label = d
        ? d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
        : `#${idx}`;
      xt.push({ label, x });
    }

    return {
      validCandles: valid,
      closes: cList,
      smaValues: smaList,
      minPrice: min,
      maxPrice: max,
      priceSpan: span,
      chartWidth: width,
      chartHeight: height,
      padding: pad,
      priceLinePoints: pPoints,
      areaPoints: aPoints,
      smaPoints: sPoints,
      yTicks: yt,
      xTicks: xt,
    };
  }, [candles]);

  if (!validCandles.length) {
    return <div className="t-status-box">{t("chart.awaiting_history")}</div>;
  }

  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // Hover position calculation
  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const relX = (clientX / rect.width) * chartWidth;
    if (relX < padding.left || relX > padding.left + innerWidth) {
      setHoverIndex(null);
      return;
    }
    const ratio = (relX - padding.left) / innerWidth;
    const idx = Math.round(ratio * (validCandles.length - 1));
    const safeIdx = Math.max(0, Math.min(idx, validCandles.length - 1));
    setHoverIndex(safeIdx);
  };

  const handleMouseLeave = () => {
    setHoverIndex(null);
  };

  const activeCandle = hoverIndex !== null ? validCandles[hoverIndex] : validCandles[validCandles.length - 1];
  const activeSMA = hoverIndex !== null ? smaValues[hoverIndex] : smaValues[smaValues.length - 1];
  const activeX =
    hoverIndex !== null
      ? padding.left + (hoverIndex / (validCandles.length - 1)) * innerWidth
      : null;
  const activeY =
    activeCandle && priceSpan
      ? padding.top + innerHeight - ((Number(activeCandle.close) - minPrice) / priceSpan) * innerHeight
      : null;

  return (
    <div className="chart-container">
      <div className="chart-header-bar">
        <div className="chart-legend">
          <span className="legend-item">
            <span className="legend-color-dot price" />
            <span>{t("chart.xau_close")}</span>
          </span>
          <span className="legend-item">
            <span className="legend-color-dot sma" />
            <span>{t("chart.sma_200")}</span>
          </span>
        </div>
        <div className="font-mono text-muted" style={{ fontSize: "11px" }}>
          {t("chart.verified_candles", { count: validCandles.length })}
        </div>
      </div>

      <div
        className="svg-chart-wrapper"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="svg-chart"
          preserveAspectRatio="none"
          role="img"
          aria-label={`${symbol} ${t("chart.price")} ${t("chart.sma_200")}`}
        >
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="90%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="smaGlow" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y-axis labels */}
          {yTicks.map((tick, i) => (
            <g key={`y-grid-${i}`}>
              <line
                x1={padding.left}
                y1={tick.y}
                x2={padding.left + innerWidth}
                y2={tick.y}
                stroke="#172233"
                strokeDasharray="3,3"
                strokeWidth="1"
              />
              <text
                x={padding.left + innerWidth + 8}
                y={tick.y + 3.5}
                fill="#64748b"
                fontSize="10"
                fontFamily="var(--font-mono)"
              >
                {tick.value.toFixed(2)}
              </text>
            </g>
          ))}

          {/* X-axis labels */}
          {xTicks.map((tick, i) => (
            <text
              key={`x-label-${i}`}
              x={tick.x}
              y={chartHeight - 6}
              fill="#64748b"
              fontSize="10"
              fontFamily="var(--font-mono)"
              textAnchor="middle"
            >
              {tick.label}
            </text>
          ))}

          {/* Area Fill */}
          {areaPoints && (
            <polygon fill="url(#areaGradient)" points={areaPoints} />
          )}

          {/* SMA 200 Line */}
          {smaPoints && (
            <polyline
              fill="none"
              stroke="#f59e0b"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="4,2"
              points={smaPoints}
            />
          )}

          {/* Price Polyline */}
          {priceLinePoints && (
            <polyline
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={priceLinePoints}
            />
          )}

          {/* Crosshair on hover */}
          {activeX !== null && activeY !== null && (
            <g>
              <line
                x1={activeX}
                y1={padding.top}
                x2={activeX}
                y2={padding.top + innerHeight}
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
              <line
                x1={padding.left}
                y1={activeY}
                x2={padding.left + innerWidth}
                y2={activeY}
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="2,2"
              />
              <circle
                cx={activeX}
                cy={activeY}
                r="4"
                fill="#10b981"
                stroke="#ffffff"
                strokeWidth="1.5"
              />
            </g>
          )}
        </svg>

        {/* Floating Tooltip Box */}
        {activeCandle && (
          <div className="chart-tooltip-box">
            <span>
              {t("chart.price")}: <strong>{Number(activeCandle.close).toFixed(2)}</strong>
            </span>
            {activeSMA !== null && (
              <span>
                {t("chart.sma_200")}: <strong style={{ color: "#f59e0b" }}>{Number(activeSMA).toFixed(2)}</strong>
              </span>
            )}
            {activeCandle.high && (
              <span className="text-muted">
                {t("chart.high_low")}: {Number(activeCandle.high).toFixed(2)} / {Number(activeCandle.low).toFixed(2)}
              </span>
            )}
            {activeCandle.timestamp && (
              <span className="text-muted">
                {new Date(activeCandle.timestamp).toLocaleString(undefined, {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

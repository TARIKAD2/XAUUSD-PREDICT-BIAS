export default function ProbabilityBar({ probabilities }) {
  if (!probabilities) return null;
  return (
    <div className="probability-bar-container">
      <div className="probability-bar">
        <div className="bar bullish" style={{width: `${probabilities.bullish * 100}%`}}></div>
        <div className="bar neutral" style={{width: `${probabilities.neutral * 100}%`}}></div>
        <div className="bar bearish" style={{width: `${probabilities.bearish * 100}%`}}></div>
      </div>
      <div className="labels">
        <span>Bullish: {(probabilities.bullish * 100).toFixed(1)}%</span>
        <span>Neutral: {(probabilities.neutral * 100).toFixed(1)}%</span>
        <span>Bearish: {(probabilities.bearish * 100).toFixed(1)}%</span>
      </div>
    </div>
  );
}
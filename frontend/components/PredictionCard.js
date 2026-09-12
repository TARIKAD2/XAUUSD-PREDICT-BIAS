import ProbabilityBar from './ProbabilityBar';
import ConfidenceBadge from './ConfidenceBadge';

export default function PredictionCard({ prediction }) {
  if (!prediction) return null;
  return (
    <div className="card prediction-card">
      <h3>AI Prediction: {prediction.symbol}</h3>
      <ConfidenceBadge confidence={prediction.confidence} />
      <p>Direction: <strong>{prediction.direction}</strong></p>
      <ProbabilityBar probabilities={prediction.probabilities} />
      <div className="reasons">
        <h4>Top Features:</h4>
        <ul>
          {prediction.top_features?.map(f => (
            <li key={f.feature}>{f.feature}: {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(4)}</li>
          ))}
        </ul>
      </div>
      <p className="model-info">Model: {prediction.model} ({prediction.model_version})</p>
    </div>
  );
}
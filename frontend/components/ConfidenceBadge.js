export default function ConfidenceBadge({ confidence }) {
  let level = 'low';
  if (confidence > 0.7) level = 'high';
  else if (confidence > 0.5) level = 'medium';
  return <span className={`badge confidence-${level}`}>Confidence: {(confidence * 100).toFixed(1)}%</span>;
}
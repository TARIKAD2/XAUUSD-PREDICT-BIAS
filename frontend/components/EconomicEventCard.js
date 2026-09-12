export default function EconomicEventCard({ item }) {
  return (
    <div className="card event-card">
      <h4>{item.title}</h4>
      <p>{new Date(item.timestamp).toLocaleString()}</p>
      <p>Actual: {item.actual} | Forecast: {item.forecast}</p>
      <p>Importance: {item.importance}</p>
    </div>
  );
}
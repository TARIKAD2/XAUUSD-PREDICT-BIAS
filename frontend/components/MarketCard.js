export default function MarketCard({ item }) {
  if (!item) return null;
  const isUp = item.change >= 0;
  return (
    <div className="card market-card">
      <h3>{item.symbol}</h3>
      <p className="price">${item.close?.toFixed(4)}</p>
      <p className={`change ${isUp ? 'up' : 'down'}`}>
        {isUp ? '▲' : '▼'} {Math.abs(item.change)?.toFixed(2)}%
      </p>
    </div>
  );
}
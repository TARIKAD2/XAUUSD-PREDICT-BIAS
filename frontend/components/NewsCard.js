export default function NewsCard({ item }) {
  return (
    <div className="card news-card">
      <h4><a href={item.url} target="_blank" rel="noreferrer">{item.title}</a></h4>
      <p className="source">{item.source} • {new Date(item.published_at).toLocaleString()}</p>
      <p className="sentiment">Sentiment: {item.sentiment}</p>
    </div>
  );
}
export default function StatusPanel({ title, message, type = 'info' }) {
  return (
    <div className={`status-panel ${type}`}>
      <h4>{title}</h4>
      <p>{message}</p>
    </div>
  );
}
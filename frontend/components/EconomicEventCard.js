import Link from "next/link";
import { useTranslation, localizeEventName } from "../context/LanguageContext";

export default function EconomicEventCard({ item }) {
  const { t } = useTranslation();
  if (!item) return null;

  const eventTitle = item.event || item.title || item.event_name || t("additional.default_event");
  const localizedTitle = localizeEventName(eventTitle, t);
  const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleString() : t("common.not_available");
  const actualStr = item.actual !== undefined && item.actual !== null ? item.actual : t("common.not_available");
  const forecastStr = item.forecast !== undefined && item.forecast !== null ? item.forecast : t("common.not_available");
  const importanceStr = item.importance ? String(item.importance).toUpperCase() : t("events.impact_medium");
  const eventId = item.id || item.event_id || item.slug || (eventTitle ? eventTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-") : null);

  return (
    <div className="event-item-card">
      <div className="event-item-header">
        <span className="event-item-title">{localizedTitle}</span>
        {eventId ? (
          <Link href={`/war-room/${eventId}`} className="enter-war-room-btn">
            {t("events.war_room_btn")}
          </Link>
        ) : null}
      </div>
      <div className="event-item-time">{timeStr}</div>
      <div className="event-metrics-row">
        <span>
          <strong>{t("events.actual")}:</strong> <span className="num-ltr">{actualStr}</span>
        </span>
        <span>•</span>
        <span>
          <strong>{t("events.forecast")}:</strong> <span className="num-ltr">{forecastStr}</span>
        </span>
        <span>•</span>
        <span>
          <strong>{t("events.importance")}:</strong> {importanceStr}
        </span>
      </div>
    </div>
  );
}
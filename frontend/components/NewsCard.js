import { useTranslation } from "../context/LanguageContext";
import { formatDateTime } from "../services/dateFormat";

export default function NewsCard({ item }) {
  const { t } = useTranslation();
  if (!item) return null;

  return (
    <div className="card news-card">
      <h4>
        {item.url ? (
          <a href={item.url} target="_blank" rel="noreferrer">
            {item.title}
          </a>
        ) : (
          item.title
        )}
      </h4>
      <p className="source">
        {item.source || t("additional.news_source")} •{" "}
        {formatDateTime(item.published_at)}
      </p>
      {item.sentiment ? <p className="sentiment">{t("news.sentiment")}: {item.sentiment}</p> : null}
    </div>
  );
}

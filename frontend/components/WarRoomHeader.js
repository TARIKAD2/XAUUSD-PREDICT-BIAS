"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { localizeEventName, useTranslation } from "../context/LanguageContext";

export default function WarRoomHeader({ eventData, liveTick, wsStatus }) {
  const { t } = useTranslation();
  const [flashClass, setFlashClass] = useState("");
  const prevPriceRef = useRef(null);

  const hasLive = liveTick && liveTick.price != null && Number.isFinite(Number(liveTick.price));
  const currentPrice = hasLive ? Number(liveTick.price) : eventData?.current_xau_price;

  useEffect(() => {
    if (!Number.isFinite(currentPrice)) return;
    if (prevPriceRef.current !== null && prevPriceRef.current !== currentPrice) {
      if (currentPrice > prevPriceRef.current) {
        setFlashClass("tick-flash-up");
      } else if (currentPrice < prevPriceRef.current) {
        setFlashClass("tick-flash-down");
      }
      const timer = setTimeout(() => setFlashClass(""), 650);
      return () => clearTimeout(timer);
    }
    prevPriceRef.current = currentPrice;
  }, [currentPrice]);

  const eventTime = eventData?.timestamp ? new Date(eventData.timestamp) : null;
  const isPast = eventTime && eventTime.getTime() < Date.now();

  const imp = (eventData?.importance || "high").toLowerCase();
  const impClass = imp.includes("high") ? "high" : imp.includes("med") ? "medium" : "low";
  const translatedStatus = {
    CONNECTED: t("status.connected"),
    CONNECTING: t("status.connecting"),
    RECONNECTING: t("status.reconnecting"),
  };
  const impactKey = imp.includes("high") ? "high" : imp.includes("med") ? "medium" : "low";

  return (
    <div className="war-room-header">
      <div className="war-room-top-nav">
        <Link href="/" className="back-link">
          ← {t("war_room.back_to_terminal")}
        </Link>
        <div className="war-room-badge-group">
          <span className="live-spot-tag">
            <span className="pulse-indicator" />
            {t("war_room.spot_live")}
          </span>
          <span className={`live-status-pill ${wsStatus === "CONNECTED" ? "live" : "connecting"}`}>
            {translatedStatus[wsStatus] || t("status.connecting")}
          </span>
        </div>
      </div>

      <div className="war-room-title-strip">
        <div className="event-primary-meta">
          <div className="event-type-tag-row">
            <span className="war-room-flair">{t("war_room.flair")}</span>
            <span className={`impact-badge ${impClass}`}>
              {t(`events.impact_${impactKey}`)}
            </span>
            <span className="country-currency-tag">
              {eventData?.country || "US"} &bull; {eventData?.currency || "USD"}
            </span>
          </div>
          <h1 className="event-headline">
            {eventData?.event_name
              ? localizeEventName(eventData.event_name, t)
              : t("additional.default_event")}
          </h1>
          <p className="event-datetime">
            {t("war_room.release_schedule")}:{" "}
            <strong>
              {eventTime ? eventTime.toUTCString() : t("additional.scheduled")}
            </strong>{" "}
            {isPast ? <span className="past-tag">({t("war_room.historical_obs")})</span> : <span className="upcoming-tag">({t("war_room.upcoming_rel")})</span>}
          </p>
        </div>

        <div className="war-room-live-box">
          <div className="live-box-label">{t("war_room.real_time_exec")}</div>
          <div className={`live-box-price ${flashClass}`}>
            {currentPrice ? `$${Number(currentPrice).toFixed(2)}` : "---.--"}
          </div>
          <div className="live-box-sub">
            {hasLive ? t("war_room.direct_tick") : t("war_room.verified_snapshot")}
          </div>
        </div>
      </div>
    </div>
  );
}

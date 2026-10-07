"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { localizeEventName, useTranslation } from "../context/LanguageContext";
import { formatDateTime } from "../services/dateFormat";

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
    DISCONNECTED: t("status.offline"),
  };
  const impactKey = imp.includes("high") ? "high" : imp.includes("med") ? "medium" : "low";

  const provMs = (() => {
    if (!liveTick) return null;
    const ts = liveTick.provider_timestamp ?? liveTick.provider_time ?? liveTick.iso_timestamp ?? liveTick.timestamp;
    if (ts == null) return null;
    if (typeof ts === "number") return ts > 1e11 ? ts : ts * 1000;
    if (typeof ts === "string") {
      const parsed = new Date(ts).getTime();
      return isNaN(parsed) ? null : parsed;
    }
    return null;
  })();

  const recvMs = (() => {
    if (!liveTick) return null;
    const ts = liveTick.received_at ?? liveTick.browser_received_at;
    if (ts == null) return null;
    if (typeof ts === "number") return ts > 1e11 ? ts : ts * 1000;
    if (typeof ts === "string") {
      const parsed = new Date(ts).getTime();
      return isNaN(parsed) ? null : parsed;
    }
    return null;
  })();

  const isConnected = wsStatus === "CONNECTED";
  let feedStatus = "OFFLINE";
  if (isConnected) {
    const now = Date.now();
    const refMs = recvMs !== null && (provMs === null || (now - provMs) <= 60000)
      ? recvMs
      : (provMs ?? recvMs);

    if (refMs !== null) {
      const ageSec = Math.max(0, (now - refMs) / 1000);
      if (ageSec < 5) feedStatus = "LIVE";
      else if (ageSec <= 30) feedStatus = "DELAYED";
      else feedStatus = "STALE";
    }
  }


  const translatedFeedStatus = {
    LIVE: t("status.live") || "LIVE",
    DELAYED: t("status.delayed") || "DELAYED",
    STALE: t("status.stale") || "STALE",
    OFFLINE: t("status.offline") || "OFFLINE",
  };

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
          <span className={`live-status-pill ${feedStatus === "LIVE" ? "live" : feedStatus === "DELAYED" ? "warning" : "connecting"}`}>
            {isConnected ? (translatedFeedStatus[feedStatus] || feedStatus) : (translatedStatus[wsStatus] || t("status.connecting"))}
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
              {eventTime ? `${formatDateTime(eventTime, { timeZone: "UTC" })} UTC` : t("additional.scheduled")}
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

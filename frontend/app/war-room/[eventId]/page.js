"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "../../../services/api";
import { formatDateTime } from "../../../services/dateFormat";
import { liveMarket } from "../../../services/liveMarket";
import WarRoomHeader from "../../../components/WarRoomHeader";
import ProbabilityGauge from "../../../components/ProbabilityGauge";
import ExpectedMetrics from "../../../components/ExpectedMetrics";
import SignalMatrix from "../../../components/SignalMatrix";
import ScenarioCards from "../../../components/ScenarioCards";
import VerdictPanel from "../../../components/VerdictPanel";
import StatusPanel from "../../../components/StatusPanel";
import { useTranslation } from "../../../context/LanguageContext";

export default function WarRoomPage() {
  const { t } = useTranslation();
  const params = useParams();
  const eventId = params?.eventId ? String(params.eventId) : null;

  const [warRoom, setWarRoom] = useState({ loading: true, data: null, error: null });
  const [liveTick, setLiveTick] = useState(null);
  const [wsStatus, setWsStatus] = useState("CONNECTING");

  // Subscribe to live WebSocket for real-time tick updates on XAU/USD
  useEffect(() => {
    const unsubscribe = liveMarket.subscribe((tick, status) => {
      if (status) {
        setWsStatus(status);
      }
      if (tick && (tick.type === "price" || tick.event === "price" || tick.type === "initial_state")) {
        const sym = (tick.symbol || tick.normalized_symbol || "").replace("/", "").toUpperCase();
        if (sym === "XAUUSD") {
          setLiveTick(tick);
        }
      }
    });
    return () => {
      unsubscribe();
    };
  }, []);

  // Fetch War Room intelligence
  useEffect(() => {
    if (!eventId) return;
    setWarRoom({ loading: true, data: null, error: null });
    api
      .warRoom(eventId)
      .then((data) => setWarRoom({ loading: false, data, error: null }))
      .catch((error) => setWarRoom({ loading: false, data: null, error }));
  }, [eventId]);

  if (warRoom.loading) {
    return (
      <main className="terminal-wrapper">
        <div style={{ padding: "40px 20px" }}>
          <StatusPanel title={t("war_room.loading_title")} message={t("war_room.loading_msg")} />
        </div>
      </main>
    );
  }

  if (warRoom.error || !warRoom.data) {
    return (
      <main className="terminal-wrapper">
        <div className="war-room-header">
          <Link href="/" className="back-link">
            ← {t("war_room.back_to_terminal")}
          </Link>
        </div>
        <div style={{ padding: "30px 20px" }}>
          <StatusPanel
            title={t("war_room.unavailable_title")}
            message={warRoom.error?.message || t("additional.unavailable_event_message")}
            type="error"
          />
        </div>
      </main>
    );
  }

  const data = warRoom.data;

  return (
    <main className="terminal-wrapper war-room-view">
      {/* Top War Room Header */}
      <WarRoomHeader eventData={data} liveTick={liveTick} wsStatus={wsStatus} />

      {/* Pre-Release Macro Context Banner */}
      <div className="war-room-context-banner">
        <div className="context-title">
          <span className="accent-bar" />
          <span>{t("war_room.pre_release_title")}</span>
        </div>
        <p className="context-text">{data.market_context}</p>
      </div>

      {/* Probability Outcome Gauge */}
      <ProbabilityGauge probabilities={data.probabilities} />

      {/* Expected Consensus Metrics */}
      <ExpectedMetrics metrics={data.expected_metrics} />

      {/* Bull / Bear Signal Matrix */}
      <SignalMatrix factors={data.signal_matrix} />

      {/* 3 Outcome Scenario Cards with Price Targets */}
      <ScenarioCards scenarios={data.scenarios} />

      {/* Executive Verdict & Risk Protocol */}
      <VerdictPanel verdict={data.verdict} />

      {/* Footer */}
      <footer className="terminal-footer">
        <div>
          {t("war_room.footer_note")}
        </div>
        <div className="font-mono text-muted">
          {t("war_room.generated")}: {formatDateTime(data.generated_at, { timeZone: "UTC" })} UTC {data.cached ? `(${t("war_room.cached")})` : `(${t("war_room.fresh_analysis")})`}
        </div>
      </footer>
    </main>
  );
}

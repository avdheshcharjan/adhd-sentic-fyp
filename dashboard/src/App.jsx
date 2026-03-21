import React from "react";
import { useBackendAPI } from "./hooks/useBackendAPI";
import MetricsCard from "./components/MetricsCard";
import FocusTimeline from "./components/FocusTimeline";
import EmotionRadar from "./components/EmotionRadar";
import WhoopCard from "./components/WhoopCard";
import InterventionLog from "./components/InterventionLog";
import WeeklyReport from "./components/WeeklyReport";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function formatDate() {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export default function App() {
  const { data, error, loading, refresh } = useBackendAPI();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <span>Connecting to ADHD Second Brain...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <span>Failed to connect: {error}</span>
        <button onClick={refresh}>Retry</button>
        <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
          Make sure the backend is running on port 8420
        </span>
      </div>
    );
  }

  const { current, daily, weekly, whoop, emotions, timeline } = data ?? {};
  const focusMinutes = daily?.total_focus_minutes;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h1>{getGreeting()}</h1>
          <span className="subtitle">
            {formatDate()}
            {focusMinutes != null &&
              ` — You've been focused for ${Math.floor(focusMinutes / 60)}h ${Math.round(focusMinutes % 60)}m today`}
          </span>
        </div>
        <div className="status">
          <span className="status-dot" />
          LIVE
        </div>
      </div>

      <div className="dashboard-grid">
        <FocusTimeline timeline={timeline} />
        <MetricsCard current={current} daily={daily} />
        <EmotionRadar emotions={emotions} />
        <WhoopCard whoop={whoop} />
        <InterventionLog daily={daily} />
        <WeeklyReport weekly={weekly} />
      </div>
    </div>
  );
}

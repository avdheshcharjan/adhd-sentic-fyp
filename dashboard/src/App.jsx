import React from "react";
import { useBackendAPI } from "./hooks/useBackendAPI";
import MetricsCard from "./components/MetricsCard";
import FocusTimeline from "./components/FocusTimeline";
import EmotionRadar from "./components/EmotionRadar";
import WhoopCard from "./components/WhoopCard";
import InterventionLog from "./components/InterventionLog";
import WeeklyReport from "./components/WeeklyReport";

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
        <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
          Make sure the backend is running on port 8420
        </span>
      </div>
    );
  }

  const { current, daily, weekly, whoop, emotions, timeline } = data ?? {};

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>ADHD Second Brain</h1>
        <span className="status">
          Live &bull; Polling every 5s
        </span>
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

import React from "react";

const fmt = (v, suffix = "") =>
  v == null ? "—" : `${typeof v === "number" ? v.toFixed(1) : v}${suffix}`;

export default function MetricsCard({ current, daily }) {
  const m = current?.metrics ?? {};
  const state = current?.behavioral_state ?? "unknown";

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Live Metrics</span>
        <span className={`state-badge ${state}`}>{state}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Context switches (5 min)</span>
        <span className="metric-value">{fmt(m.context_switch_rate_5min)}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Focus score</span>
        <span className="metric-value">{fmt(m.focus_score, "%")}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Distraction ratio</span>
        <span className="metric-value">{fmt(m.distraction_ratio, "%")}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Current streak</span>
        <span className="metric-value">
          {fmt(m.current_streak_minutes, " min")}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Active app</span>
        <span className="metric-value" style={{ fontSize: "0.9rem" }}>
          {current?.current_app || "—"}
        </span>
      </div>

      {daily && (
        <>
          <div
            className="card-subtitle"
            style={{ marginTop: 12, marginBottom: 4 }}
          >
            Today
          </div>
          <div className="metric-row">
            <span className="metric-label">Focus time</span>
            <span className="metric-value">
              {fmt(daily.total_focus_minutes, " min")}
            </span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Active time</span>
            <span className="metric-value">
              {fmt(daily.total_active_minutes, " min")}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

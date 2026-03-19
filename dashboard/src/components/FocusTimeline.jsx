import React from "react";

const STATE_COLORS = {
  focused: "var(--green)",
  distracted: "var(--red)",
  neutral: "var(--yellow)",
  idle: "#3f3f46",
};

export default function FocusTimeline({ timeline }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="card full-width">
        <div className="card-header">
          <span className="card-title">Today's Focus Timeline</span>
        </div>
        <div className="empty-state">No activity recorded yet today.</div>
      </div>
    );
  }

  const totalSec = timeline.reduce((s, b) => s + b.duration_sec, 0);

  return (
    <div className="card full-width">
      <div className="card-header">
        <span className="card-title">Today's Focus Timeline</span>
        <span className="card-subtitle">
          {Math.round(totalSec / 60)} min tracked
        </span>
      </div>

      <div className="timeline-bar">
        {timeline.map((block, i) => {
          const pct = (block.duration_sec / totalSec) * 100;
          return (
            <div
              key={i}
              className={`timeline-segment ${block.state}`}
              style={{ width: `${pct}%` }}
              title={`${block.app} — ${block.category} (${Math.round(block.duration_sec / 60)} min)`}
            />
          );
        })}
      </div>

      <div className="timeline-legend">
        {Object.entries(STATE_COLORS).map(([state, color]) => (
          <span key={state}>
            <span className="legend-dot" style={{ background: color }} />
            {state}
          </span>
        ))}
      </div>
    </div>
  );
}

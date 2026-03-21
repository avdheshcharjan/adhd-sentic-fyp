import React from "react";

const STATE_COLORS = {
  focused: "var(--focused)",
  hyperfocused: "var(--hyperfocused)",
  distracted: "var(--distracted)",
  multitasking: "var(--neutral)",
  idle: "var(--text-tertiary)",
};

export default function InterventionLog({ daily }) {
  const triggered = daily?.interventions_triggered ?? 0;
  const accepted = daily?.interventions_accepted ?? 0;
  const states = daily?.behavioral_states ?? {};

  const acceptRate =
    triggered > 0 ? ((accepted / triggered) * 100).toFixed(0) : "—";

  const sortedStates = Object.entries(states).sort((a, b) => b[1] - a[1]);

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Interventions</span>
        <span className="card-subtitle">Today</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Triggered</span>
        <span className="metric-value">{triggered}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Accepted</span>
        <span className="metric-value">{accepted}</span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Acceptance rate</span>
        <span
          className="metric-value"
          style={{ color: "var(--focused)" }}
        >
          {acceptRate}%
        </span>
      </div>

      {sortedStates.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="section-label">Behavioral states (min)</div>
          <div style={{ display: "flex", gap: 8 }}>
            {sortedStates.slice(0, 4).map(([state, minutes]) => (
              <div className="stat-tile" key={state}>
                <span
                  className="stat-tile-value"
                  style={{ color: STATE_COLORS[state] ?? "var(--text-primary)" }}
                >
                  {minutes}
                </span>
                <span className="stat-tile-label">
                  {state.length > 8 ? state.slice(0, 8) + "." : state}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

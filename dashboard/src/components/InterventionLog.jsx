import React from "react";

export default function InterventionLog({ daily }) {
  const triggered = daily?.interventions_triggered ?? 0;
  const accepted = daily?.interventions_accepted ?? 0;
  const states = daily?.behavioral_states ?? {};

  // Build summary from daily data since we don't have individual intervention records in dashboard payload
  const acceptRate =
    triggered > 0 ? ((accepted / triggered) * 100).toFixed(0) : "—";

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
        <span className="metric-value">{acceptRate}%</span>
      </div>

      {Object.keys(states).length > 0 && (
        <>
          <div
            className="card-subtitle"
            style={{ marginTop: 12, marginBottom: 4 }}
          >
            Behavioral states (minutes)
          </div>
          {Object.entries(states)
            .sort((a, b) => b[1] - a[1])
            .map(([state, minutes]) => (
              <div className="metric-row" key={state}>
                <span className="metric-label">
                  <span className={`state-badge ${state}`}>{state}</span>
                </span>
                <span className="metric-value">{minutes} min</span>
              </div>
            ))}
        </>
      )}
    </div>
  );
}

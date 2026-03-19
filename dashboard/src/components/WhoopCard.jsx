import React from "react";

const TIER_EMOJI = { green: "🟢", yellow: "🟡", red: "🔴" };

export default function WhoopCard({ whoop }) {
  if (!whoop) {
    return (
      <div className="card">
        <div className="card-header">
          <span className="card-title">Whoop Recovery</span>
        </div>
        <div className="empty-state">
          Whoop data unavailable. Run{" "}
          <code>whoopskill auth login</code> to connect.
        </div>
      </div>
    );
  }

  const tier = whoop.recovery_tier ?? "yellow";

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Whoop Recovery</span>
        <span className={`tier-${tier}`} style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          {TIER_EMOJI[tier]} {whoop.recovery_score ?? "—"}%
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">HRV (rMSSD)</span>
        <span className="metric-value">
          {whoop.hrv_rmssd != null ? `${whoop.hrv_rmssd.toFixed(1)} ms` : "—"}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Resting HR</span>
        <span className="metric-value">
          {whoop.resting_hr != null ? `${whoop.resting_hr.toFixed(0)} bpm` : "—"}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Sleep performance</span>
        <span className="metric-value">
          {whoop.sleep_performance != null
            ? `${whoop.sleep_performance.toFixed(0)}%`
            : "—"}
        </span>
      </div>

      <div className="metric-row">
        <span className="metric-label">Recommended focus block</span>
        <span className="metric-value">
          {whoop.recommended_focus_block_minutes ?? "—"} min
        </span>
      </div>

      {whoop.sleep_notes && whoop.sleep_notes.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="card-subtitle" style={{ marginBottom: 4 }}>
            Sleep notes
          </div>
          {whoop.sleep_notes.map((note, i) => (
            <div
              key={i}
              style={{ fontSize: "0.8rem", color: "var(--text-dim)", padding: "2px 0" }}
            >
              {note}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

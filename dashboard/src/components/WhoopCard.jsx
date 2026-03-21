import React from "react";

const TIER_COLOR = {
  green: "var(--success)",
  yellow: "var(--neutral)",
  red: "var(--warm-amber)",
};

export default function WhoopCard({ whoop }) {
  if (!whoop) {
    return (
      <div className="card">
        <div className="card-header">
          <span className="card-title">Whoop Recovery</span>
        </div>
        <div className="empty-state">
          Whoop data unavailable. Connect your Whoop band in Settings.
        </div>
      </div>
    );
  }

  const tier = whoop.recovery_tier ?? "yellow";
  const tierColor = TIER_COLOR[tier] ?? TIER_COLOR.yellow;

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Whoop Recovery</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: tierColor,
              display: "inline-block",
            }}
          />
          <span
            style={{
              fontSize: "1.25rem",
              fontWeight: 700,
              color: tierColor,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {whoop.recovery_score ?? "—"}%
          </span>
        </div>
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
        <span
          className="metric-value"
          style={{ color: "var(--primary)" }}
        >
          {whoop.recommended_focus_block_minutes ?? "—"} min
        </span>
      </div>
    </div>
  );
}

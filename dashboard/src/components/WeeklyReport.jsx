import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function WeeklyReport({ weekly }) {
  if (!weekly) {
    return (
      <div className="card full-width">
        <div className="card-header">
          <span className="card-title">Weekly Report</span>
        </div>
        <div className="empty-state">No weekly data available.</div>
      </div>
    );
  }

  const chartData = (weekly.daily_focus_scores ?? []).map((d) => ({
    date: d.date?.slice(5) ?? "",
    Focus: d.focus_pct ?? 0,
    Distraction: d.distraction_pct ?? 0,
  }));

  const trend = weekly.trend ?? "stable";

  return (
    <div className="card full-width">
      <div className="card-header">
        <span className="card-title">Weekly Report</span>
        <span className={`trend-badge ${trend}`}>
          {trend === "improving"
            ? "Improving"
            : trend === "declining"
              ? "Needs attention"
              : "Stable"}
        </span>
      </div>

      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData} barGap={2}>
            <CartesianGrid
              stroke="var(--outline-variant)"
              strokeDasharray="3 3"
              strokeOpacity={0.4}
            />
            <XAxis
              dataKey="date"
              stroke="var(--text-tertiary)"
              fontSize={11}
              fontFamily="Lexend"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="var(--text-tertiary)"
              fontSize={11}
              fontFamily="Lexend"
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface-container-high)",
                border: "none",
                borderRadius: 10,
                fontSize: "0.75rem",
                fontFamily: "Lexend, sans-serif",
              }}
              formatter={(v) => `${v.toFixed(1)}%`}
            />
            <Legend
              wrapperStyle={{ fontSize: "0.6875rem", fontFamily: "Lexend" }}
            />
            <Bar
              dataKey="Focus"
              fill="var(--focused)"
              radius={[4, 4, 0, 0]}
            />
            <Bar
              dataKey="Distraction"
              fill="var(--distracted)"
              radius={[4, 4, 0, 0]}
              fillOpacity={0.6}
            />
          </BarChart>
        </ResponsiveContainer>
      )}

      <div className="stats-grid" style={{ marginTop: 16 }}>
        <div className="metric-row">
          <span className="metric-label">Avg focus</span>
          <span className="metric-value">
            {weekly.avg_focus_percentage?.toFixed(1)}%
          </span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Avg distraction</span>
          <span className="metric-value">
            {weekly.avg_distraction_percentage?.toFixed(1)}%
          </span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Total interventions</span>
          <span className="metric-value">{weekly.total_interventions}</span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Acceptance rate</span>
          <span className="metric-value">
            {weekly.intervention_acceptance_rate?.toFixed(1)}%
          </span>
        </div>
      </div>

      {(weekly.best_focus_day || weekly.worst_focus_day) && (
        <div
          style={{
            display: "flex",
            gap: 16,
            marginTop: 8,
            fontSize: "0.75rem",
            color: "var(--text-tertiary)",
          }}
        >
          {weekly.best_focus_day && <span>Best: {weekly.best_focus_day}</span>}
          {weekly.worst_focus_day && (
            <span>Needs attention: {weekly.worst_focus_day}</span>
          )}
        </div>
      )}

      {weekly.top_apps_weekly && weekly.top_apps_weekly.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="section-label">Top apps</div>
          {weekly.top_apps_weekly.map((app) => (
            <div className="metric-row" key={app.app_name}>
              <span className="metric-label">
                {app.app_name}{" "}
                <span style={{ fontSize: "0.625rem", opacity: 0.6 }}>
                  {app.category}
                </span>
              </span>
              <span
                className="metric-value"
                style={{ fontSize: "0.875rem" }}
              >
                {app.minutes} min ({app.percentage}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

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
    date: d.date?.slice(5) ?? "", // MM-DD
    Focus: d.focus_pct ?? 0,
    Distraction: d.distraction_pct ?? 0,
  }));

  const trend = weekly.trend ?? "stable";

  return (
    <div className="card full-width">
      <div className="card-header">
        <span className="card-title">Weekly Report</span>
        <span className={`trend-badge ${trend}`}>
          {trend === "improving" ? "Improving" : trend === "declining" ? "Declining" : "Stable"}
        </span>
      </div>

      {chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} barGap={2}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="var(--text-dim)" fontSize={12} />
            <YAxis
              stroke="var(--text-dim)"
              fontSize={12}
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: "0.8rem",
              }}
              formatter={(v) => `${v.toFixed(1)}%`}
            />
            <Legend wrapperStyle={{ fontSize: "0.8rem" }} />
            <Bar dataKey="Focus" fill="var(--green)" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Distraction" fill="var(--red)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 16 }}>
        <div className="metric-row" style={{ borderBottom: "none" }}>
          <span className="metric-label">Avg focus</span>
          <span className="metric-value">{weekly.avg_focus_percentage?.toFixed(1)}%</span>
        </div>
        <div className="metric-row" style={{ borderBottom: "none" }}>
          <span className="metric-label">Avg distraction</span>
          <span className="metric-value">{weekly.avg_distraction_percentage?.toFixed(1)}%</span>
        </div>
        <div className="metric-row" style={{ borderBottom: "none" }}>
          <span className="metric-label">Total interventions</span>
          <span className="metric-value">{weekly.total_interventions}</span>
        </div>
        <div className="metric-row" style={{ borderBottom: "none" }}>
          <span className="metric-label">Acceptance rate</span>
          <span className="metric-value">{weekly.intervention_acceptance_rate?.toFixed(1)}%</span>
        </div>
      </div>

      {(weekly.best_focus_day || weekly.worst_focus_day) && (
        <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: "0.8rem", color: "var(--text-dim)" }}>
          {weekly.best_focus_day && <span>Best: {weekly.best_focus_day}</span>}
          {weekly.worst_focus_day && <span>Worst: {weekly.worst_focus_day}</span>}
        </div>
      )}

      {weekly.top_apps_weekly && weekly.top_apps_weekly.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="card-subtitle" style={{ marginBottom: 4 }}>Top apps</div>
          {weekly.top_apps_weekly.map((app) => (
            <div className="metric-row" key={app.app_name}>
              <span className="metric-label">
                {app.app_name}{" "}
                <span style={{ fontSize: "0.7rem", opacity: 0.6 }}>{app.category}</span>
              </span>
              <span className="metric-value" style={{ fontSize: "0.9rem" }}>
                {app.minutes} min ({app.percentage}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

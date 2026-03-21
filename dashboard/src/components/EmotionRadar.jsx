import React, { useMemo } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const DIMENSIONS = [
  { key: "introspection", label: "Pleasantness" },
  { key: "temper", label: "Attention" },
  { key: "sensitivity", label: "Sensitivity" },
  { key: "attitude", label: "Aptitude" },
];

export default function EmotionRadar({ emotions }) {
  const { chartData, avg } = useMemo(() => {
    if (!emotions || emotions.length === 0) {
      const emptyAvg = {};
      DIMENSIONS.forEach((d) => { emptyAvg[d.key] = 0; });
      return {
        chartData: DIMENSIONS.map((d) => ({ axis: d.label, value: 50 })),
        avg: emptyAvg,
      };
    }

    const recent = emotions.slice(0, 10);
    const computed = {};

    for (const dim of DIMENSIONS) {
      const values = recent
        .map((e) => e.emotion_profile?.[dim.key])
        .filter((v) => v != null);
      computed[dim.key] =
        values.length > 0
          ? values.reduce((a, b) => a + b, 0) / values.length
          : 0;
    }

    return {
      chartData: DIMENSIONS.map((d) => ({
        axis: d.label,
        value: Math.round((computed[d.key] + 100) / 2),
        raw: Math.round(computed[d.key]),
      })),
      avg: computed,
    };
  }, [emotions]);

  const primaryEmotion = emotions?.[0]?.emotion_profile?.primary_emotion;

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Emotion Radar</span>
        {primaryEmotion && (
          <span className="card-subtitle">Current: {primaryEmotion}</span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={chartData} outerRadius="70%">
          <PolarGrid stroke="var(--outline-variant)" />
          <PolarAngleAxis dataKey="axis" />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            dataKey="value"
            stroke="var(--primary)"
            fill="var(--primary)"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface-container-high)",
              border: "none",
              borderRadius: 10,
              fontSize: "0.75rem",
              fontFamily: "Lexend, sans-serif",
            }}
            formatter={(value, _name, props) => [
              `${props.payload.raw ?? value}`,
              props.payload.axis,
            ]}
          />
        </RadarChart>
      </ResponsiveContainer>

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        {DIMENSIONS.map((d) => (
          <div className="stat-tile" key={d.key}>
            <span
              className="stat-tile-value"
              style={{ color: "var(--primary)" }}
            >
              {Math.round((avg[d.key] + 100) / 2)}
            </span>
            <span className="stat-tile-label">
              {d.label.length > 8 ? d.label.slice(0, 8) + "." : d.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

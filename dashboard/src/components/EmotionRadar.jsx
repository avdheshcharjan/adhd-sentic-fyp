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

// Map SenticNet Hourglass dimensions to display labels
const DIMENSIONS = [
  { key: "introspection", label: "Pleasantness", positive: "Joy", negative: "Sadness" },
  { key: "temper", label: "Attention", positive: "Interest", negative: "Disgust" },
  { key: "sensitivity", label: "Sensitivity", positive: "Fear", negative: "Anger" },
  { key: "attitude", label: "Aptitude", positive: "Trust", negative: "Surprise" },
];

export default function EmotionRadar({ emotions }) {
  const chartData = useMemo(() => {
    if (!emotions || emotions.length === 0) {
      return DIMENSIONS.map((d) => ({ axis: d.label, value: 50 }));
    }

    // Average the most recent emotions (up to 10)
    const recent = emotions.slice(0, 10);
    const avg = {};

    for (const dim of DIMENSIONS) {
      const values = recent
        .map((e) => e.emotion_profile?.[dim.key])
        .filter((v) => v != null);
      avg[dim.key] = values.length > 0
        ? values.reduce((a, b) => a + b, 0) / values.length
        : 0;
    }

    return DIMENSIONS.map((d) => ({
      axis: d.label,
      // Normalize from [-100, 100] to [0, 100] for the radar
      value: Math.round((avg[d.key] + 100) / 2),
      raw: Math.round(avg[d.key]),
    }));
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

      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={chartData} outerRadius="70%">
          <PolarGrid stroke="var(--border)" />
          <PolarAngleAxis dataKey="axis" />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            dataKey="value"
            stroke="var(--accent)"
            fill="var(--accent)"
            fillOpacity={0.25}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: "0.8rem",
            }}
            formatter={(value, name, props) => [
              `${props.payload.raw ?? value}`,
              props.payload.axis,
            ]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

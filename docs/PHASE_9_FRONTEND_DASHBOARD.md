# Phase 9: Frontend Dashboard

> **Timeline**: Week 7–8  
> **Dependencies**: Phase 1 (backend API), all other phases for data  
> **Status**: Optional but valuable for FYP demonstration

---

## Overview

A React web dashboard showing real-time ADHD metrics, emotion visualization, Whoop physiological data, and intervention logs. Built with Vite + React + Recharts for fast development and rich data visualization.

---

## Dashboard Components

### 1. FocusTimeline (`FocusTimeline.jsx`)

Horizontal timeline showing today's activity color-coded by category.

| Color | State | Examples |
|-------|-------|---------|
| 🟢 Green | Focused | development, writing, research |
| 🔴 Red | Distracted | social_media, entertainment |
| 🟡 Yellow | Multitasking | Rapid switching between productive apps |
| ⚪ Gray | Idle | No input detected |

Similar to Rize's daily activity view.

### 2. EmotionRadar (`EmotionRadar.jsx`)

Recharts radar chart displaying the current Hourglass of Emotions state.

**4 axes**:
- **Pleasantness** (joy ↔ sadness)
- **Attention** (interest ↔ disgust)
- **Sensitivity** (fear ↔ anger)
- **Aptitude** (trust ↔ surprise)

### 3. WhoopCard (`WhoopCard.jsx`)

Card displaying:
- Recovery score with green/yellow/red color indicator
- HRV (rmssd)
- Sleep performance percentage
- Recommended focus block length for today
- Sleep notes (if any concerns)

### 4. MetricsCard (`MetricsCard.jsx`)

Real-time display of:
- Context switch rate (per 5 min)
- Focus score (0–100%)
- Distraction ratio (0–100%)
- Current streak time
- Behavioral state label (focused / distracted / etc.)

### 5. InterventionLog (`InterventionLog.jsx`)

- List of today's interventions
- What was suggested (acknowledgment + suggestion)
- What the user chose (action or dismissed)
- Effectiveness trends over time

### 6. WeeklyReport (`WeeklyReport.jsx`)

- Weekly pattern aggregation
- Focus time trends
- Most productive hours
- Intervention effectiveness rates
- Emotional patterns summary

---

## API Endpoint

```
GET http://localhost:8420/insights/dashboard
```

Returns all data needed for the dashboard in a single call.

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **Vite** | Build tool + dev server |
| **React** | UI framework |
| **Recharts** | Charts (radar, timeline, bar) |
| **Custom hooks** | `useBackendAPI.js` for data fetching |

---

## Key Files

| File | Purpose |
|------|---------|
| `dashboard/package.json` | Dependencies |
| `dashboard/vite.config.js` | Vite configuration |
| `dashboard/src/App.jsx` | Main app layout |
| `dashboard/src/components/FocusTimeline.jsx` | Daily activity timeline |
| `dashboard/src/components/EmotionRadar.jsx` | Hourglass emotion radar |
| `dashboard/src/components/WhoopCard.jsx` | Recovery/sleep card |
| `dashboard/src/components/InterventionLog.jsx` | Intervention history |
| `dashboard/src/components/WeeklyReport.jsx` | Weekly pattern summary |
| `dashboard/src/hooks/useBackendAPI.js` | API data fetching hook |

---

## Verification Checklist

- [ ] Dashboard loads and connects to backend
- [ ] FocusTimeline shows today's activity with correct colors
- [ ] EmotionRadar displays 4 Hourglass dimensions
- [ ] WhoopCard shows recovery tier with correct color
- [ ] MetricsCard updates in real-time
- [ ] InterventionLog shows today's interventions
- [ ] Dashboard is responsive and visually polished for FYP demo

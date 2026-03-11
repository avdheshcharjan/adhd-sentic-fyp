---
name: morning-briefing
description: Daily ADHD-optimized morning briefing from Whoop recovery data
triggers:
  - morning briefing
  - how did I sleep
  - morning report
  - recovery
---

# ADHD Morning Briefing

Delivers an ADHD-tailored morning briefing based on Whoop physiological data. Triggered automatically at 7:30 AM via HEARTBEAT, or on-demand when the user asks about their morning status.

## How to Fetch Data

```
GET http://localhost:8420/whoop/morning-briefing
```

The response contains:
- `recovery_score` (0-100)
- `recovery_tier` ("green" | "yellow" | "red")
- `recommended_focus_block_minutes` (15 | 25 | 45)
- `sleep_performance` (percentage)
- `sleep_notes` (list of observations)
- `hrv_rmssd`, `resting_hr`, `sws_percentage`, `rem_percentage`

## Message Templates

Format your reply based on the `recovery_tier`:

### Green (recovery 67-100%)
"Good morning! Your body recovered well ({recovery_score}%). Great day for challenging work. Try {recommended_focus_block_minutes}-min focus blocks."

If there are sleep notes, add ONE relevant observation.

### Yellow (recovery 34-66%)
"Morning! Moderate recovery ({recovery_score}%). Pace yourself — {recommended_focus_block_minutes}-min focus blocks with breaks."

If sleep performance is below 70%, mention it gently.

### Red (recovery 0-33%)
"Hey, take it easy today. Recovery is low ({recovery_score}%). Stick to easy tasks, {recommended_focus_block_minutes}-min focus blocks."

Add a self-compassion note: "Low recovery happens. Being kind to yourself today IS productive."

## Rules

- Keep it to 2-3 sentences max
- Never guilt the user about poor sleep
- Frame recommendations positively

## Error Handling

If Whoop data is unavailable (503 or 401):
- Reply: "Couldn't fetch your Whoop data this morning. No worries — start with 25-min focus blocks and check in with yourself."

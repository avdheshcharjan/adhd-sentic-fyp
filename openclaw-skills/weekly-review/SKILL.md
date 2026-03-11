---
name: weekly-review
description: Weekly ADHD pattern summary with focus trends and insights
triggers:
  - weekly review
  - how was my week
  - weekly summary
  - weekly patterns
---

# Weekly ADHD Pattern Review

Delivers a 7-day behavioral pattern summary. Triggered automatically on Sundays at 8 PM via HEARTBEAT, or on-demand.

## How to Fetch Data

```
GET http://localhost:8420/insights/weekly
```

The response contains:
- `avg_focus_percentage` (0-100)
- `avg_distraction_percentage` (0-100)
- `total_interventions` (count)
- `intervention_acceptance_rate` (0-100%)
- `best_focus_day` (date string)
- `worst_focus_day` (date string)
- `top_apps_weekly` (list of {app_name, minutes, percentage})
- `trend` ("improving" | "declining" | "stable")
- `daily_focus_scores` (list of {date, focus_pct, distraction_pct})

## Message Format

Structure the weekly review as a brief summary:

### Opening (based on trend)
- **Improving**: "Your week showed real progress!"
- **Stable**: "Solid, consistent week. Here's the snapshot:"
- **Declining**: "This week was tough, and that's okay. Here's what happened:"

### Key Stats (pick 2-3 most relevant)
- "Average focus: {avg_focus_percentage}%"
- "Best day: {best_focus_day}" (only if notably better)
- "You used {interventions} interventions and found {acceptance_rate}% helpful"

### One Actionable Insight
Based on the data, offer ONE specific, actionable observation:
- If top distraction app is social media: "Instagram took {X} min this week. Maybe try putting it in a different room during focus blocks?"
- If trend is improving: "Whatever you did on {best_focus_day} worked — try to recreate those conditions."
- If trend is declining: "Rest is productive too. Consider a lighter schedule next week."

## Rules

- Total message: 3-4 sentences max
- Lead with validation, not metrics
- ONE actionable takeaway (not a list of improvements)
- Never compare to previous weeks negatively
- Celebrate small wins explicitly

## Error Handling

If backend is unreachable:
- Reply: "Couldn't pull your weekly data. Take a moment to reflect: what went well this week? What's one thing you'd adjust?"

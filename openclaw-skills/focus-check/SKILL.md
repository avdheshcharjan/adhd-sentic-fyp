---
name: focus-check
description: On-demand ADHD focus status check with current metrics
triggers:
  - how am I doing
  - am I focused
  - focus check
  - what's my status
  - how's my focus
---

# Focus Status Check

Returns the user's current ADHD behavioral metrics on demand. Gives a quick, honest, non-judgmental snapshot of their focus state.

## How to Fetch Data

```
GET http://localhost:8420/insights/current
```

The response contains:
- `behavioral_state` ("focused" | "distracted" | "multitasking" | "hyperfocused" | "idle")
- `metrics.focus_score` (0-100%)
- `metrics.distraction_ratio` (0-1)
- `metrics.context_switch_rate_5min` (count)
- `metrics.current_streak_minutes` (minutes on current app)
- `metrics.hyperfocus_detected` (boolean)
- `current_app` (app name)
- `current_category` (category)

## Message Templates

### Focused
"You're doing great! {current_streak_minutes} min focused on {current_app}. Keep the flow going."

### Distracted
"Looks like things are a bit scattered — {context_switch_rate_5min} app switches in the last 5 min. Want to pick one thing to focus on for 10 minutes?"

### Multitasking
"You're bouncing between a few things. That's okay! Maybe pick the most important one and give it 15 minutes?"

### Hyperfocused
"You've been locked in on {current_app} for {current_streak_minutes} min — impressive! Just a gentle check: have you had water or stretched recently?"

### Idle
"Looks like you're on a break. When you're ready, try starting with the smallest next step."

## Rules

- One message, 1-2 sentences max
- Always validate before suggesting
- Never guilt about distraction
- If hyperfocused, gently remind about self-care without breaking flow
- Use upward framing always

## Error Handling

If backend is unreachable:
- Reply: "Can't check your metrics right now. If you're feeling scattered, try this: pick ONE task, set a 10-min timer, and just start."

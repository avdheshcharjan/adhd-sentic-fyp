# Phase 8: OpenClaw Integration — Design

> Approved: 2026-03-11

## Summary

Connect the ADHD Second Brain backend to Telegram and WhatsApp via OpenClaw custom skills. Implement full `/insights/*` endpoints. Create HEARTBEAT.md scheduling.

## Part 1: Backend — Shared State Module

Move `ADHDMetricsEngine` singleton from `api/screen.py` to `services/shared_state.py` so both `screen.py` and `insights.py` can access it.

## Part 2: Backend — Full `/insights/*` Endpoints

### `/insights/current`
- Returns live metrics from in-memory engine
- Current app, category, behavioral state
- Pending intervention (if any)
- Whoop recovery tier (if connected)

### `/insights/daily`
- Query `ActivityLog` for today's entries
- Compute: total focus time, distraction %, top apps, interventions triggered/accepted
- Include Whoop data if available

### `/insights/weekly`
- Query `ActivityLog` for last 7 days
- Daily focus scores, best/worst days
- Intervention effectiveness trends
- Behavioral pattern summary

## Part 3: OpenClaw Skills (4 SKILL.md files)

### `adhd-vent/SKILL.md`
- Forward messages to `POST localhost:8420/chat/message`
- Check `used_llm` field — if false, surface crisis resources
- Relay `response` and `suggested_actions` back to user
- Communication rules: ≤2-3 sentences, validate before suggest

### `morning-briefing/SKILL.md`
- Fetch `GET localhost:8420/whoop/morning-briefing`
- Format by recovery tier (green/yellow/red templates)
- Triggered by HEARTBEAT at 7:30 AM

### `focus-check/SKILL.md`
- Fetch `GET localhost:8420/insights/current`
- Format as ADHD-friendly status message
- On-demand when user asks "How am I doing?"

### `weekly-review/SKILL.md`
- Fetch `GET localhost:8420/insights/weekly`
- Format as pattern summary
- Triggered by HEARTBEAT on Sundays at 8 PM

## Part 4: HEARTBEAT.md

Scheduling config for OpenClaw:
- Morning briefing: 7:30 AM daily
- Focus check: every 30 min during 9 AM - 10 PM (only if actionable)
- Weekly review: Sunday 8 PM

## Part 5: OpenClaw Installation & Config

- Install OpenClaw (npm)
- Configure Telegram + WhatsApp connectors
- Link custom skills directory

## Alignment with Phase 7

- Chat endpoint already returns `ChatResponse` with all needed fields
- Morning briefing endpoint already returns structured data with recovery tier
- Safety handling (crisis detection) already works — skill checks `used_llm=false`
- System prompt already enforces ADHD communication rules
- `ChatInput.context` field available for platform metadata

# Phase 8: OpenClaw Integration (Chat Interface)

> **Timeline**: Week 6–7  
> **Dependencies**: Phase 1 (backend), Phase 3 (SenticNet), Phase 7 (MLX)  
> **Requirements**: Node.js 22+ (for OpenClaw), Telegram/WhatsApp account

---

## Overview

OpenClaw provides the messaging gateway for Telegram and WhatsApp. Custom "skills" connect to the ADHD Second Brain backend, enabling venting/emotional regulation support, morning briefings, focus status checks, and weekly reviews — all through familiar chat interfaces.

---

## Custom Skills

### 1. Venting Chat Skill (`adhd-vent`)

**When used**: User sends emotional or venting messages via Telegram/WhatsApp.

**Pipeline**:
1. Forward message to `POST /chat/message` on the backend
2. Backend runs full SenticNet 13-API pipeline
3. Safety check runs FIRST (depression + toxicity)
4. LLM generates empathetic response with SenticNet context
5. Memory stores emotional patterns for personalization

**Communication Rules** (ADHD-friendly):
- Under 2–3 sentences (working memory deficits)
- Validate before suggesting
- Offer 2–3 choices maximum
- Use upward framing

**Critical safety handling**:
- If `CRITICAL` safety level → do NOT be a therapist
- Acknowledge pain → provide crisis resources (988 Lifeline) → encourage professional support

### 2. Morning Briefing Skill (`morning-briefing`)

**When used**: Automatically every morning at 7:30 AM (via HEARTBEAT.md).

**Pipeline**:
1. Fetch `GET /whoop/morning-briefing` from backend
2. Format as ADHD-friendly message based on recovery tier

**Message Templates**:

| Tier | Template |
|------|----------|
| 🟢 Green | "Good morning! Your body recovered well (X%). Great day for challenging work. Try 45-min focus blocks." |
| 🟡 Yellow | "Morning! Moderate recovery (X%). Pace yourself — 25-min focus blocks with breaks." |
| 🔴 Red | "Hey, take it easy today. Recovery is low (X%). Stick to easy tasks, 15-min focus blocks." |

### 3. Focus Check Skill (`focus-check`)

**When used**: User asks "How am I doing?" or "Am I focused?"

**Pipeline**: Fetch `GET /insights/current` → format current metrics.

### 4. Weekly Review Skill (`weekly-review`)

**When used**: Automatically every Sunday at 8 PM (via HEARTBEAT.md).

**Pipeline**: Fetch `GET /insights/weekly` → format pattern summary.

---

## HEARTBEAT.md Configuration

```markdown
## Every morning at 7:30 AM:
- Fetch Whoop morning briefing from localhost:8420/whoop/morning-briefing
- Deliver formatted ADHD morning briefing to user

## Every 30 minutes during active hours (9 AM - 10 PM):
- Check localhost:8420/insights/current for any pending alerts
- Only message if there's something actionable

## Every Sunday at 8 PM:
- Fetch weekly review from localhost:8420/insights/weekly
- Deliver formatted weekly ADHD pattern summary
```

---

## Key Files

| File | Purpose |
|------|---------|
| `openclaw-skills/adhd-vent/SKILL.md` | Venting chat skill definition |
| `openclaw-skills/morning-briefing/SKILL.md` | Morning briefing skill |
| `openclaw-skills/focus-check/SKILL.md` | On-demand focus status |
| `openclaw-skills/weekly-review/SKILL.md` | Weekly pattern review |

---

## Verification Checklist

- [ ] OpenClaw installed and configured for Telegram/WhatsApp
- [ ] Venting messages processed through full SenticNet pipeline
- [ ] Safety-critical messages trigger crisis resource response
- [ ] Morning briefing delivered at 7:30 AM via HEARTBEAT
- [ ] Focus check returns current metrics on demand
- [ ] Weekly review delivered on Sunday evenings
- [ ] Responses are ≤ 2–3 sentences

---

## Next Phase

→ [Phase 9: Frontend Dashboard](PHASE_9_FRONTEND_DASHBOARD.md)

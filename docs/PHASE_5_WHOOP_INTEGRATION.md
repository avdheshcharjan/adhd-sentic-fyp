# Phase 5: Whoop Integration

> **Timeline**: Week 5–6  
> **Dependencies**: Phase 1 (backend + database)  
> **External**: Whoop developer account, OAuth credentials

---

## Overview

Integrates Whoop physiological data (HRV, sleep stages, recovery score) to generate ADHD-tailored morning briefings and context-aware recommendations. Recovery scores map directly to executive function predictions for the day.

---

## Whoop API v2

- **Base URL**: `https://api.prod.whoop.com/developer`
- **Auth**: OAuth 2.0 Authorization Code flow
- **Key endpoints**: `/v1/recovery`, `/v1/cycle`, `/v1/activity/sleep`
- **Scopes**: `read:recovery read:sleep read:cycles read:profile read:body_measurement`

---

## OAuth 2.0 Flow

```
1. GET /whoop/auth
   → Redirect to Whoop consent screen

2. User grants access
   → Whoop redirects to GET /whoop/callback?code=XXX

3. Exchange code for tokens
   → POST https://api.prod.whoop.com/oauth/oauth2/token

4. Store access + refresh tokens securely
```

### API Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/whoop/auth` | Start OAuth flow (redirect to Whoop) |
| `GET` | `/whoop/callback` | OAuth callback (exchange code for token) |
| `GET` | `/whoop/morning-briefing` | Generate ADHD morning briefing |

---

## Recovery-to-ADHD Mapping

| Recovery Tier | Score Range | Color | EF Impact | Recommended Focus Blocks | Strategy |
|---------------|------------|-------|-----------|--------------------------|----------|
| **Green** | 67–100% | 🟢 | Optimal | 45 min | Deep, challenging work |
| **Yellow** | 34–66% | 🟡 | Moderate | 25 min | Structured pacing, extra structure |
| **Red** | 0–33% | 🔴 | Impaired | 15 min | Easy tasks, frequent breaks, written lists |

## Sleep-to-ADHD Mapping

| Sleep Metric | Threshold | ADHD Impact | Recommendation |
|-------------|-----------|-------------|----------------|
| **Low SWS (deep sleep)** | < 15% | Working memory issues | Use written over verbal |
| **High disturbances** | > 5 | Fragmented attention | Shorter focus blocks |
| **Low HRV** | < 40ms | Emotion regulation harder | Extra grace, grounding exercises |

---

## Morning Briefing Output

```json
{
    "date": "2026-03-08",
    "recovery_score": 72,
    "recovery_tier": "green",
    "hrv_rmssd": 65,
    "resting_hr": 52,
    "sleep_performance": 85,
    "sws_percentage": 18.5,
    "rem_percentage": 22.3,
    "disturbance_count": 2,
    "focus_recommendation": "Great recovery — today is optimal for deep, challenging work.",
    "recommended_focus_block_minutes": 45,
    "sleep_notes": [],
    "strain_yesterday": 12.5
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/services/whoop_service.py` | Whoop API client + morning briefing logic |
| `backend/api/whoop.py` | OAuth flow + briefing endpoint |
| `backend/models/whoop_data.py` | Pydantic models for Whoop data |
| `backend/db/repositories/whoop_repo.py` | PostgreSQL persistence |

---

## Prerequisites

1. Register at [developer.whoop.com](https://developer.whoop.com)
2. Create an application, get `client_id` and `client_secret`
3. Set redirect URI to `http://localhost:8420/whoop/callback`
4. Add credentials to `.env`

---

## Verification Checklist

- [ ] OAuth flow redirects to Whoop and back successfully
- [ ] Access + refresh tokens stored securely
- [ ] Recovery data fetched correctly
- [ ] Sleep data includes SWS and disturbance counts
- [ ] Morning briefing generates correct tier (green/yellow/red)
- [ ] Sleep notes generated for low SWS, high disturbances, low HRV
- [ ] Data persisted to `whoop_data` PostgreSQL table

---

## Next Phase

→ [Phase 6: Memory System](PHASE_6_MEMORY_SYSTEM.md)

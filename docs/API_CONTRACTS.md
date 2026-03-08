# API Contracts

> Full endpoint reference for the Python FastAPI backend (`localhost:8420`).

---

## Endpoint Summary

| Method | Endpoint | Purpose | Latency Target | Phase |
|--------|----------|---------|----------------|-------|
| `POST` | `/screen/activity` | Report screen state (called every 2s) | <100ms | 1 |
| `POST` | `/chat/message` | Process venting/chat message | <3s | 3 |
| `GET` | `/whoop/auth` | Start Whoop OAuth flow | redirect | 5 |
| `GET` | `/whoop/callback` | OAuth callback | <1s | 5 |
| `GET` | `/whoop/morning-briefing` | Generate morning briefing | <2s | 5 |
| `GET` | `/insights/current` | Current ADHD state + metrics | <50ms | 1 |
| `GET` | `/insights/daily` | Today's summary | <500ms | 1 |
| `GET` | `/insights/weekly` | Weekly pattern review | <2s | 1 |
| `GET` | `/insights/dashboard` | Full dashboard data | <500ms | 9 |
| `GET` | `/interventions/current` | Any pending intervention | <50ms | 4 |
| `POST` | `/interventions/{id}/respond` | Record user response | <100ms | 4 |
| `GET` | `/health` | Backend health check | <10ms | 1 |

---

## Detailed Endpoint Contracts

### `POST /screen/activity`

**Called by**: Swift Menu Bar App (every 2 seconds)

**Request**:
```json
{
    "app_name": "Google Chrome",
    "window_title": "YouTube - Funny Cats",
    "url": "https://youtube.com/watch?v=abc",
    "is_idle": false,
    "timestamp": "2026-03-08T12:00:00Z"
}
```

**Response** (< 100ms):
```json
{
    "category": "entertainment",
    "metrics": {
        "context_switch_rate_5min": 8,
        "focus_score": 45.2,
        "distraction_ratio": 0.55,
        "current_streak_minutes": 3.2,
        "hyperfocus_detected": false,
        "behavioral_state": "multitasking"
    },
    "intervention": null
}
```

**When intervention is triggered**:
```json
{
    "category": "social_media",
    "metrics": { ... },
    "intervention": {
        "type": "distraction_spiral",
        "ef_domain": "self_restraint",
        "acknowledgment": "Looks like things are scattered right now — that's okay.",
        "suggestion": "A 2-minute reset could help you refocus. What feels right?",
        "actions": [
            {"id": "breathe", "emoji": "🫁", "label": "Breathing exercise"},
            {"id": "task_pick", "emoji": "🎯", "label": "Pick one task"},
            {"id": "break", "emoji": "☕", "label": "Take a break"}
        ],
        "requires_senticnet": false
    }
}
```

---

### `POST /chat/message`

**Called by**: OpenClaw (Telegram/WhatsApp) or Dashboard

**Request**:
```json
{
    "text": "I am so frustrated I cant focus on anything today",
    "conversation_id": "optional-uuid",
    "context": {"source": "openclaw"}
}
```

**Response** (< 3s):
```json
{
    "response": "It sounds like focus is really fighting against you today...",
    "emotion_profile": {
        "primary_emotion": "frustration",
        "hourglass_dimensions": {
            "pleasantness": -0.6,
            "attention": -0.3,
            "sensitivity": 0.8,
            "aptitude": -0.4
        },
        "polarity": "negative",
        "polarity_score": -72.5,
        "is_subjective": true,
        "sarcasm_score": 5.2,
        "sarcasm_detected": false
    },
    "safety_flags": {
        "level": "normal",
        "depression_score": 25.0,
        "toxicity_score": 10.0,
        "intensity_score": -65.0,
        "is_critical": false
    },
    "suggested_actions": [
        {"id": "vent_more", "emoji": "💬", "label": "Tell me more"},
        {"id": "ground", "emoji": "🌿", "label": "Grounding exercise"}
    ]
}
```

---

### `GET /whoop/morning-briefing`

**Called by**: OpenClaw HEARTBEAT (7:30 AM daily)

**Response** (< 2s):
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

### `GET /insights/current`

**Response** (< 50ms):
```json
{
    "metrics": { ... },
    "behavioral_state": "focused",
    "pending_intervention": null,
    "current_session": {
        "app": "Visual Studio Code",
        "duration_minutes": 25.5,
        "category": "development"
    }
}
```

---

### `POST /interventions/{id}/respond`

**Request**:
```json
{
    "action_taken": "breathe",
    "dismissed": false,
    "effectiveness_rating": 4
}
```

**Response** (< 100ms):
```json
{
    "status": "recorded",
    "cooldown_seconds": 300
}
```

---

### `GET /health`

**Response** (< 10ms):
```json
{
    "status": "healthy",
    "version": "0.1.0",
    "database": "connected",
    "uptime_seconds": 3600
}
```

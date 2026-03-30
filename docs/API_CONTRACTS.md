# API Contracts

> Full endpoint reference for the Python FastAPI backend (`localhost:8420`).
> **Version**: 1.0.0 | **Last Updated**: 2026-03-30

---

## Endpoint Summary

### Core

| Method | Endpoint | Purpose | Latency Target |
|--------|----------|---------|----------------|
| `GET` | `/health` | Backend health check | <10ms |
| `POST` | `/screen/activity` | Report screen state (called every 2-3s by Swift app) | <100ms |
| `POST` | `/chat/message` | Process venting/chat message through full pipeline | <3s |

### Insights

| Method | Endpoint | Purpose | Latency Target |
|--------|----------|---------|----------------|
| `GET` | `/insights/current` | Current ADHD state + metrics | <50ms |
| `GET` | `/insights/daily` | Today's summary (optional `?date=YYYY-MM-DD`) | <500ms |
| `GET` | `/insights/weekly` | Weekly pattern review | <2s |
| `GET` | `/insights/dashboard` | Full dashboard data | <500ms |

### Focus & Tasks

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/tasks/create` | Create task + start focus session |
| `GET` | `/api/v1/tasks/current` | Current active task |
| `POST` | `/api/v1/tasks/{id}/complete` | Complete a task |
| `POST` | `/api/v1/focus/toggle` | Toggle focus session |
| `GET` | `/api/v1/focus/session` | Focus session state |
| `GET` | `/api/v1/focus/off-task` | Off-task detection status |

### Brain Dump

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/brain-dump/` | Capture brain dump (store in Mem0) |
| `POST` | `/api/v1/brain-dump/stream` | Capture + stream AI summary (SSE) |
| `GET` | `/api/v1/brain-dump/review/recent` | Recent brain dumps |
| `GET` | `/api/v1/brain-dump/review/session/{session_id}` | Session brain dumps |

### Vent Chat

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/vent/chat/stream` | Vent chat with SSE streaming |
| `POST` | `/api/v1/vent/chat` | Vent chat (non-streaming fallback) |
| `POST` | `/api/v1/vent/session/new` | Clear vent session |

### Notch Island (Swift)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/emotion/current` | Current behavioral state |
| `GET` | `/api/v1/interventions/pending` | Pending intervention (Swift-shaped) |
| `POST` | `/api/v1/interventions/{id}/acknowledge` | Acknowledge intervention |
| `GET` | `/api/v1/progress/today` | Daily progress (tasks/focus) |
| `GET` | `/api/v1/dashboard/stats` | Dashboard stats with PASE scores |
| `GET` | `/api/v1/dashboard/weekly` | Weekly report |
| `GET` | `/api/v1/dashboard/history` | Snapshot list for date range |
| `GET` | `/api/v1/dashboard/history/{date}` | Full snapshot for a date |
| `POST` | `/api/v1/dashboard/snapshot` | Manual snapshot trigger |
| `POST` | `/api/v1/capture` | Quick capture (thought/idea) |
| `GET` | `/api/v1/calendar/upcoming` | Google Calendar upcoming events |

### Interventions

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/interventions/current` | Any pending intervention |
| `POST` | `/interventions/{id}/respond` | Record user response |
| `POST` | `/interventions/correct-concept` | XAI concept correction |

### Integrations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/auth/whoop` | Whoop auth (whoopskill CLI) |
| `GET` | `/api/auth/whoop/status` | Whoop connection status |
| `POST` | `/api/auth/whoop/disconnect` | Disconnect Whoop |
| `GET` | `/whoop/recovery` | Fetch latest recovery data |
| `GET` | `/whoop/sleep` | Sleep data |
| `GET` | `/whoop/cycle` | Cycle data |
| `GET` | `/whoop/morning-briefing` | Generate morning briefing |
| `GET` | `/api/auth/google` | Google OAuth redirect |
| `GET` | `/api/auth/google/callback` | Google OAuth callback |
| `GET` | `/api/auth/google/status` | Google Calendar connection status |
| `POST` | `/api/auth/google/revoke` | Revoke Google Calendar |

### Evaluation

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/eval/ablation` | Toggle SenticNet ablation mode (A/B evaluation) |
| `GET` | `/eval/ablation` | Get current ablation status |
| `POST` | `/eval/logging` | Toggle evaluation interaction logging |

---

## Detailed Endpoint Contracts

### `POST /screen/activity`

**Called by**: Swift Menu Bar App (every 2-3 seconds)

**Request**:
```json
{
    "app_name": "Google Chrome",
    "window_title": "YouTube - Funny Cats",
    "url": "https://youtube.com/watch?v=abc",
    "is_idle": false,
    "timestamp": "2026-03-08T12:00:00Z",
    "off_task_alerts_enabled": true,
    "off_task_alerts_always": false
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
    "intervention": null,
    "off_task": false
}
```

**With intervention + off-task detection**:
```json
{
    "category": "social_media",
    "metrics": { "..." : "..." },
    "intervention": {
        "type": "distraction_spiral",
        "ef_domain": "self_restraint",
        "acknowledgment": "Looks like things are scattered right now — that's okay.",
        "suggestion": "A 2-minute reset could help you refocus. What feels right?",
        "actions": [
            {"id": "breathe", "emoji": "\ud83e\ude81", "label": "Breathing exercise"},
            {"id": "task_pick", "emoji": "\ud83c\udfaf", "label": "Pick one task"},
            {"id": "break", "emoji": "\u2615", "label": "Take a break"}
        ],
        "notification_tier": 3,
        "explanation": {
            "tier_1": {"color": "amber"},
            "tier_2": "Your attention has been jumping around...",
            "tier_3": "..."
        }
    },
    "off_task": true
}
```

**Notes**: SetFit emotion classification runs inline (<50ms) mapping window title to 6 ADHD states. SenticNet enrichment runs asynchronously in background.

---

### `POST /chat/message`

**Called by**: Telegram Bot or Dashboard

**Request**:
```json
{
    "text": "I am so frustrated I cant focus on anything today",
    "conversation_id": "optional-uuid"
}
```

**Response** (< 3s):
```json
{
    "response": "That sounds really tough — not being able to focus...",
    "emotion_profile": {
        "primary_emotion": "frustration",
        "hourglass_dimensions": {
            "pleasantness": -0.6,
            "attention": -0.3,
            "sensitivity": 0.8,
            "aptitude": -0.4
        },
        "polarity_score": -72.5,
        "intensity_score": -65.0
    },
    "safety_flags": null,
    "suggested_actions": [
        {"id": "vent_more", "emoji": "\ud83d\udcac", "label": "Tell me more"},
        {"id": "ground", "emoji": "\ud83c\udf3f", "label": "Grounding exercise"}
    ],
    "used_llm": true,
    "thinking_mode": "think",
    "emotion_context": {
        "polarity": -0.725,
        "mood_tags": ["frustration"],
        "hourglass_pleasantness": -0.6,
        "hourglass_attention": -0.3,
        "hourglass_sensitivity": 0.8,
        "hourglass_aptitude": -0.4,
        "sentic_concepts": ["failure", "focus", "inability"]
    },
    "ablation_mode": false,
    "latency_ms": 4250.0,
    "token_count": 87
}
```

**Safety-critical response** (depression > 70 AND toxicity > 60):
```json
{
    "response": "I hear you. If things feel really heavy, these people can help:\n\n- SOS CareText: text HOME to 9151 0000\n- IMH Helpline: 6389 2222 (24hr)\n- 988 Suicide & Crisis Lifeline: dial 988",
    "used_llm": false,
    "thinking_mode": null,
    "ablation_mode": false
}
```

---

### `POST /api/v1/brain-dump/`

**Called by**: Swift Brain Dump modal (Cmd+Shift+B)

**Request**:
```json
{
    "content": "Just remembered I need to email the professor about the deadline extension",
    "session_id": "optional-focus-session-id"
}
```

**Response**:
```json
{
    "id": "bd_abc123",
    "status": "captured",
    "emotional_state": "anxious",
    "timestamp": "2026-03-30T14:00:00Z"
}
```

### `POST /api/v1/brain-dump/stream`

Same request body. Returns SSE stream:
```
data: {"type": "captured", "id": "bd_abc123", "emotional_state": "anxious"}

data: {"type": "summary", "token": "You"}
data: {"type": "summary", "token": " need"}
data: {"type": "summary", "token": " to"}
...
data: [DONE]
```

---

### `POST /api/v1/vent/chat/stream`

**Called by**: Swift Vent modal (Cmd+Shift+V) or Telegram Bot

**Request**:
```json
{
    "message": "Everything is falling apart and I can't cope",
    "session_id": "vent_session_123",
    "history": [
        {"role": "user", "content": "I'm so stressed"},
        {"role": "assistant", "content": "I hear you..."}
    ]
}
```

**Response**: SSE stream:
```
data: {"token": "I"}
data: {"token": " can"}
data: {"token": " see"}
...
data: [DONE]
```

**Crisis detection**: If crisis keywords detected, returns immediate crisis resources (no LLM).

### `POST /api/v1/vent/chat`

Same request, non-streaming fallback:
```json
{
    "response": "I can see this is really overwhelming...",
    "is_crisis": false
}
```

---

### `POST /api/v1/tasks/create`

**Called by**: Swift Task Creation modal (Cmd+Shift+T)

**Request**:
```json
{
    "name": "Write literature review section",
    "duration_seconds": 1800,
    "start_focus": true
}
```

**Response**:
```json
{
    "id": "uuid-here",
    "name": "Write literature review section",
    "duration_seconds": 1800,
    "progress": 0.0,
    "is_active": true,
    "created_at": "2026-03-30T14:00:00Z",
    "completed_at": null
}
```

---

### `GET /api/v1/dashboard/stats`

**Called by**: Swift Notch Island expanded panel

**Response**:
```json
{
    "total_focus_minutes": 142,
    "total_active_minutes": 285,
    "interventions_triggered": 5,
    "interventions_accepted": 3,
    "focus_timeline": [
        {"id": "a1b2c3", "category": "focused", "duration": 0.45},
        {"id": "d4e5f6", "category": "distracted", "duration": 0.15},
        {"id": "g7h8i9", "category": "idle", "duration": 0.40}
    ],
    "emotion_scores": {
        "pleasantness": 0.55,
        "attention": 0.72,
        "sensitivity": 0.38,
        "aptitude": 0.61
    }
}
```

---

### `GET /api/v1/interventions/pending`

**Called by**: Swift Notch Island alert state

**Response** (when pending):
```json
{
    "id": "intervention-uuid",
    "title": "Looks like things are scattered right now — that's okay.",
    "body": "A 2-minute reset could help you refocus.",
    "emoji": "\ud83e\ude81",
    "action_label": "Breathing exercise",
    "notification_tier": 3
}
```

**Response** (no pending): `null`

---

### `GET /api/v1/calendar/upcoming`

**Called by**: Swift Notch Island calendar strip

**Query params**: `?limit=3`

**Response**:
```json
[
    {
        "summary": "Team standup",
        "start": "2026-03-30T14:00:00+08:00",
        "end": "2026-03-30T14:30:00+08:00",
        "location": "Zoom"
    }
]
```

Returns `[]` if Google Calendar not authenticated.

---

### `GET /whoop/morning-briefing`

**Called by**: Telegram Bot scheduler (7:30 AM daily)

**Response**:
```json
{
    "date": "2026-03-30",
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
    "strain_yesterday": 12.5
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

**Response**:
```json
{
    "status": "recorded",
    "cooldown_seconds": 300
}
```

---

### `GET /health`

**Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected",
    "uptime_seconds": 3600
}
```

---

### `POST /eval/ablation`

**Request**:
```json
{
    "enabled": true
}
```

**Response**:
```json
{
    "ablation_mode": true,
    "message": "SenticNet ablation mode enabled — LLM will receive vanilla ADHD coaching prompt"
}
```

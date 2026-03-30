# ADHD Second Brain — System Architecture

> **Version**: 1.0.0 | **Last Updated**: 2026-03-30
> **Target**: macOS (Apple Silicon M1+), single-user, local-first

---

## Overview

The ADHD Second Brain is an always-on macOS personal AI assistant that monitors screen activity, detects ADHD behavioral patterns, processes data through SenticNet's 13 affective computing APIs, classifies emotions via a contrastive fine-tuned SetFit model, generates coaching responses with an on-device Qwen3-4B LLM, and delivers explainable, evidence-based interventions via a Concept Bottleneck XAI architecture. A native Telegram bot provides proactive outreach (morning briefings, focus checks, weekly reviews) alongside on-demand venting.

### Key Capabilities
- **Screen monitoring** — active app, window title, browser URL, idle state (every 2-3s)
- **ADHD pattern detection** — context switching, distraction spirals, hyperfocus, procrastination
- **Affective computing** — SenticNet 13-API pipeline for emotion, safety, engagement analysis
- **SetFit emotion classification** — contrastive fine-tuned all-mpnet-base-v2 mapping to 6 ADHD states (86% accuracy)
- **On-device LLM coaching** — Qwen3-4B-4bit via Apple MLX (~2.3GB, loaded on demand, unloaded after 2min idle)
- **Explainable interventions** — Concept Bottleneck Model with counterfactual explanations
- **Physiological data** — Whoop integration via `whoopskill` CLI for HRV, sleep, recovery
- **Telegram bot** — native `python-telegram-bot` v21 for venting, morning briefings, focus checks, weekly reviews
- **Notch Island** — 5-state macOS notch widget (Dormant, Ambient, Glanceable, Expanded, Alert)
- **Brain Dump** — floating modal for thought capture with AI summarization via MLX, stored in Mem0
- **Vent modal** — floating panel with 4-layer safety system and SSE streaming
- **Focus sessions** — task creation (Cmd+Shift+T), focus timer, off-task detection via embedding similarity
- **Google Calendar** — OAuth 2.0 integration, upcoming events in Notch calendar strip
- **Daily snapshots** — auto-saved at 23:55, backfilled on startup, browsable in History view
- **Long-term memory** — Mem0 (backed by pgvector) + PostgreSQL pattern tracking

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S MACBOOK                               │
│                                                                     │
│  ┌──────────────────────────┐     ┌──────────────────────────────┐  │
│  │  Swift macOS App         │────▶│  Python FastAPI Backend       │  │
│  │  (Notch Island +         │◀────│  (localhost:8420)             │  │
│  │   Modals + Monitors)     │     │                              │  │
│  │  ~25MB RAM               │     │  ├── SenticNet Pipeline      │  │
│  └──────────────────────────┘     │  ├── SetFit Emotion Classifier│  │
│                                   │  ├── JITAI Decision Engine   │  │
│  ┌──────────────────────────┐     │  ├── Whoop Service (CLI)     │  │
│  │  Telegram Bot            │────▶│  ├── MLX Qwen3-4B Inference  │  │
│  │  (python-telegram-bot)   │◀────│  ├── Memory (Mem0 + PG)      │  │
│  │  Embedded in backend     │     │  ├── XAI Explanation Engine  │  │
│  │  lifespan                │     │  ├── Google Calendar Service  │  │
│  └──────────────────────────┘     │  └── Snapshot Service        │  │
│                                   │  ~500MB RAM (+ ~2.3GB when   │  │
│                                   │   LLM loaded on demand)      │  │
│                                   └──────────────────────────────┘  │
│                                            │                        │
│                                  ┌─────────▼──────────┐            │
│                                  │  PostgreSQL + pgvec │            │
│                                  │  (Docker, port 5433)│            │
│                                  └────────────────────┘             │
│                                            │                        │
│                                  ┌─────────▼──────────┐            │
│                                  │  SenticNet Cloud    │            │
│                                  │  Google Calendar API│            │
│                                  │  Telegram Bot API   │            │
│                                  └────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. User Interface Layer

| Component | Technology | Role | Resource Usage |
|-----------|-----------|------|----------------|
| **Swift macOS App** | Native Swift / SwiftUI, macOS 14+ | Notch Island, floating modals (BrainDump, Vent, TaskCreation), screen monitoring, intervention delivery | ~25MB RAM |
| **Telegram Bot** | `python-telegram-bot` v21, embedded in backend lifespan | Venting (default text handler), morning briefing, focus check, weekly review, scheduled push messages | Part of backend process |
| **React Dashboard** | Vite 5 + React 18 + Recharts | Focus timeline, emotion radar, Whoop card, metrics, intervention log, weekly report | Optional |

### 2. Python FastAPI Backend (`localhost:8420`)

The backend is the **central brain** — all interfaces are thin clients that call it.

| Subsystem | Key Files | Purpose |
|-----------|-----------|---------|
| **API Routes** | `api/health.py`, `screen.py`, `chat.py`, `whoop.py`, `insights.py`, `interventions.py`, `evaluation.py`, `notch.py`, `google_auth.py`, `brain_dump.py`, `vent.py` | REST endpoints (12 routers) |
| **Activity Classifier** | `services/activity_classifier.py` | 5-layer app/URL/title/embedding classification |
| **SetFit Emotion Classifier** | `services/emotion_classifier_setfit.py`, `services/setfit_service.py` | Contrastive fine-tuned all-mpnet-base-v2 → 6 ADHD emotion states (86%), singleton at startup |
| **ADHD Metrics Engine** | `services/adhd_metrics.py` | Rolling window behavioral metrics |
| **JITAI Engine** | `services/jitai_engine.py` | Barkley's 5 EF-domain intervention rules with 4-gate system |
| **XAI Explainer** | `services/xai_explainer.py` | Concept Bottleneck + counterfactual explanations |
| **SenticNet Pipeline** | `services/senticnet_pipeline.py`, `services/senticnet_client.py` | 4-tier 13-API orchestration |
| **MLX Inference** | `services/mlx_inference.py` | Qwen3-4B-4bit on Apple Silicon, load-on-demand, 2min idle unload |
| **Chat Processor** | `services/chat_processor.py` | Full pipeline: SenticNet → Safety → LLM → Memory |
| **Vent Service** | `services/vent_service.py` | 4-layer safety vent pipeline, SSE streaming |
| **Brain Dump Service** | `services/brain_dump_service.py` | Thought capture + AI summarization via MLX + Mem0 storage |
| **Focus Service** | `services/focus_service.py`, `services/focus_relevance.py` | Task creation, focus timer, off-task detection via embedding similarity |
| **Snapshot Service** | `services/snapshot_service.py` | Daily metric aggregation, auto-save at 23:55 |
| **Insights Service** | `services/insights_service.py` | Dashboard analytics |
| **Google Calendar** | `services/google_calendar.py` | OAuth 2.0 + event fetching |
| **Whoop Service** | `services/whoop_service.py` | Wraps `whoopskill` CLI |
| **Memory Service** | `services/memory_service.py` | Mem0 (pgvector) + PostgreSQL |
| **Behavioral Analysis** | `services/hyperfocus_classifier.py`, `transition_detector.py`, `adaptive_frequency.py` | Hyperfocus detection, transitions, adaptive polling |
| **Notification** | `services/notification_tier.py`, `action_suggestions.py` | 5-tier notification logic, action suggestions |
| **Telegram Bot** | `telegram_bot/bot.py`, `scheduler.py`, `handlers/` | Bot factory, cron jobs, 5 command handlers |
| **Evaluation** | `services/evaluation_logger.py` | Ablation + interaction logging (36-field JSONL) |

### 3. Data Layer

| Store | Technology | Contents |
|-------|-----------|----------|
| **PostgreSQL + pgvector** | Docker (`pgvector/pgvector:pg16`, port 5433) | Activities, SenticNet analyses, interventions, Whoop data, focus tasks, behavioral patterns, daily snapshots, Mem0 vector embeddings |

**Database Tables** (from `db/models.py`):

| Model | Table | Key Fields |
|-------|-------|------------|
| `ActivityLog` | `activities` | app_name, window_title, url, category, is_idle, timestamp, metrics JSONB |
| `SenticAnalysis` | `senticnet_analyses` | text, source, emotion_profile, safety_flags, adhd_signals |
| `InterventionHistory` | `interventions` | intervention_type, trigger_reason, user_response, effectiveness_score |
| `WhoopLog` | `whoop_data` | date, recovery_score, sleep_score, strain_score, metrics JSONB |
| `FocusTask` | `focus_tasks` | name, duration_seconds, progress, is_active, created_at, completed_at |
| `BehavioralPattern` | `behavioral_patterns` | pattern_type, description, confidence, embedding Vector(1536) |
| `DailySnapshot` | `daily_snapshots` | date, focus/distraction minutes, context_switches, top_apps, emotion_scores, whoop_recovery |

### 4. External Services

| Service | Purpose | Auth |
|---------|---------|------|
| **SenticNet Cloud** | 13 affective computing endpoints | API keys (IP-locked) |
| **Whoop** | Recovery, sleep, strain data | `whoopskill` CLI (OAuth 2.0) |
| **Google Calendar** | Upcoming events for Notch calendar strip | OAuth 2.0 |
| **Telegram Bot API** | Push messages and command handling | Bot token |

All LLM inference is **on-device** via Apple MLX. No cloud LLM APIs are used.

---

## Data Flow — Screen Monitoring (Hot Path)

```
Swift App (2-3s polling)
    │
    ▼ POST /screen/activity (<100ms target)
    │
    ├── 1. Activity Classifier (5-layer, <25ms worst case)
    │       L0: User corrections (highest priority)
    │       L1: App name lookup (~70%, <1ms)
    │       L2: URL domain lookup (~20%, <1ms)
    │       L3: Title keywords (~8%, <2ms)
    │       L4: Embedding similarity (~2%, <25ms, all-MiniLM-L6-v2)
    │
    ├── 2. SetFit Emotion Classification
    │       Maps activity context → 6 ADHD states → PASE radar profile
    │
    ├── 3. Focus Relevance Check (if focus session active)
    │       Embedding similarity between task name and current activity
    │
    ├── 4. ADHD Metrics Engine (in-memory, <1ms)
    │       Context switch rate, focus score, distraction ratio, streak
    │
    ├── 5. JITAI Engine (rule engine, <2ms)
    │       Check Barkley's 5 EF domains → generate intervention or null
    │
    └── 6. Background Tasks (async, non-blocking)
            ├── Persist to PostgreSQL
            └── Enrich with SenticNet (if intervention needs it)
```

## Data Flow — Chat/Venting (Warm Path)

```
Telegram Bot / Vent Modal / Dashboard
    │
    ▼ POST /api/v1/vent/chat/stream (SSE) or POST /chat/message
    │
    ├── Layer 1: Crisis keyword detection (exact substring match)
    │       ↳ If triggered → immediate crisis resources response
    │
    ├── Layer 2: SenticNet semantic analysis (4-tier)
    │       Safety → Emotion → ADHD Signals → Deep (if needed)
    │
    ├── Layer 3: LLM Generation (Qwen3-4B via MLX)
    │       SenticNet context injected into system prompt
    │       SSE stream tokens to client
    │
    ├── Layer 4: Output safety check (post-generation)
    │       Filter unsafe patterns
    │
    └── Memory Storage (Mem0 + PostgreSQL)
```

## Data Flow — Brain Dump

```
Brain Dump Modal (Cmd+Shift+B)
    │
    ▼ POST /api/v1/brain-dump/stream
    │
    ├── Store in Mem0 (type=brain_dump, session_id, emotional_state)
    └── AI summary via MLX Qwen3-4B → SSE stream response
```

## Data Flow — Focus Session

```
Task Creation Modal (Cmd+Shift+T)
    │
    ▼ POST /api/v1/tasks/create
    │
    ├── Create FocusTask in PostgreSQL
    ├── Focus timer starts
    ├── Screen activity checks embedding similarity against task name
    └── Off-task detection feeds into JITAI intervention decisions
```

---

## Background Tasks

| Task | Interval | Purpose |
|------|----------|---------|
| **Model cleanup loop** | Every 30s | Unloads MLX LLM after 2min idle to free ~2.3GB |
| **Daily snapshot loop** | Every 60s | Saves end-of-day snapshot at 23:55, backfills yesterday on startup |
| **Telegram bot** | Continuous polling | Handles commands/messages + scheduled jobs |

### Telegram Scheduled Jobs

| Job | Schedule | Handler |
|-----|----------|---------|
| Morning briefing | Daily 07:30 | Whoop recovery + agenda |
| Focus check | Every 30 min | Current focus state + nudge |
| Weekly review | Sunday 20:00 | Week summary + patterns |

---

## On-Device Models

| Model | Size | Usage | Loading |
|-------|------|-------|---------|
| **all-MiniLM-L6-v2** | ~80MB | Activity classifier L4, focus relevance | Always resident |
| **all-mpnet-base-v2 (SetFit)** | ~420MB | Emotion classification → 6 ADHD states | Singleton at startup |
| **Qwen3-4B-4bit** | ~2.3GB | Coaching, vent responses, brain dump summaries | Load on demand, unload after 2min idle |
| **SenticNet Python** | ~50MB | 400K concepts for local emotion lookup | Always resident |

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **macOS** | 14+ (Sonoma) | 15+ (Sequoia) |
| **Chip** | Apple M1 | Apple M3/M4 |
| **RAM** | 8GB | 16GB (for MLX models) |
| **Python** | 3.11 | 3.11 |
| **PostgreSQL** | 16 + pgvector | via Docker (port 5433) |
| **Xcode** | 15+ | 16+ |

---

## Swift App Structure

```
swift-app/ADHDSecondBrain/
├── NotchIsland/               # 5-state macOS notch widget
│   ├── States/                # Dormant, Ambient, Glanceable, Expanded, Alert
│   ├── Components/            # CalendarStrip, EmotionGlow, TaskCard, TimerRing, ...
│   └── Animations/            # Blur, Pulse, ReducedMotion
├── Modals/                    # Floating panels
│   ├── BrainDump/             # Cmd+Shift+B
│   ├── Vent/                  # Cmd+Shift+V
│   ├── TaskCreation/          # Cmd+Shift+T
│   └── Shared/                # HotkeyDefinitions, VisualEffectBackground
├── Monitors/                  # Screen, Browser, Idle, Transition
├── UI/                        # Dashboard, History, Settings, Onboarding, MenuBar
├── Networking/                # BackendClient (port 8420)
├── Services/                  # NotchCoordinator, HoverTracker, KeyboardShortcuts
├── Notifications/             # TierManager (5-tier calm notification)
├── DesignSystem/              # Tokens, animations, spacing
└── Models/                    # EmotionState, NotchModels
```

### Notch Island States

| State | Trigger | Visual |
|-------|---------|--------|
| **Dormant** | Default | Invisible, matches system notch |
| **Ambient** | Background awareness | Subtle emotion glow border |
| **Glanceable** | Hover | Compact: timer ring, emotion, task card |
| **Expanded** | Click | Full panel: calendar strip, mode switcher, quick capture |
| **Alert** | Intervention | Overlay with intervention banner |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Data Models](DATA_MODELS.md) | Database schemas + Pydantic models |
| [API Contracts](API_CONTRACTS.md) | Full endpoint reference (~40 endpoints) |
| [Testing Strategy](TESTING_STRATEGY.md) | Unit tests + evaluation suite |
| [SenticNet Mapping](SENTICNET_MAPPING.md) | SenticNet API → ADHD mapping |
| [XAI Framework](XAI_FRAMEWORK.md) | Explainability architecture |
| [UML Diagrams](models-fyp/adhd-second-brain-diagrams.md) | Master component + sequence diagrams |
| [Phase Plans](plans/) | Phase 1-9 build plans |

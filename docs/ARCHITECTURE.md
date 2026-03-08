# ADHD Second Brain — System Architecture

> **Version**: 0.1.0 | **Last Updated**: 2026-03-08  
> **Target**: macOS (Apple Silicon M1+), single-user, local-first

---

## Overview

The ADHD Second Brain is an always-on macOS personal AI assistant that monitors screen activity, detects ADHD behavioral patterns, processes data through SenticNet's 13 affective computing APIs, and delivers explainable, evidence-based interventions via a Concept Bottleneck XAI architecture.

### Key Capabilities
- **Screen monitoring** — active app, window title, browser URL, idle state (every 2–3s)
- **ADHD pattern detection** — context switching, distraction spirals, hyperfocus, procrastination
- **Affective computing** — SenticNet 13-API pipeline for emotion, safety, engagement analysis
- **Explainable interventions** — Concept Bottleneck Model with counterfactual explanations
- **Physiological data** — Whoop integration for HRV, sleep, recovery-driven recommendations
- **Emotional regulation** — venting/chat via OpenClaw (Telegram/WhatsApp)
- **Long-term memory** — pattern tracking, intervention effectiveness, user preferences

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER'S MACBOOK                              │
│                                                                 │
│  ┌──────────────────────┐     ┌──────────────────────────────┐  │
│  │  Swift Menu Bar App  │────▶│  Python FastAPI Backend       │  │
│  │  (Screen Monitor +   │◀────│  (localhost:8420)             │  │
│  │   Notification UI)   │     │                              │  │
│  │  ~25MB RAM           │     │  ├── SenticNet Pipeline      │  │
│  └──────────────────────┘     │  ├── JITAI Decision Engine   │  │
│                               │  ├── Whoop Service           │  │
│  ┌──────────────────────┐     │  ├── MLX Model Inference     │  │
│  │  OpenClaw Gateway    │────▶│  ├── Memory (Mem0 + PG)      │  │
│  │  (Telegram/WhatsApp) │◀────│  └── XAI Explanation Engine  │  │
│  │  Optional interface  │     │  ~500MB RAM (with models)    │  │
│  └──────────────────────┘     └──────────────────────────────┘  │
│                                         │                       │
│                               ┌─────────▼──────────┐           │
│                               │  PostgreSQL + pgvec │           │
│                               │  SQLite (cache)     │           │
│                               └────────────────────┘            │
│                                         │                       │
│                               ┌─────────▼──────────┐           │
│                               │  Whoop Cloud API    │           │
│                               │  SenticNet Cloud    │           │
│                               └────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. User Interface Layer

| Component | Technology | Role | Resource Usage |
|-----------|-----------|------|----------------|
| **Swift Menu Bar App** | Native Swift / SwiftUI | Screen capture, intervention popups, focus sessions | ~25MB RAM |
| **OpenClaw Gateway** | Node.js (Telegram/WhatsApp) | Venting chat, morning briefings, weekly reviews | Optional |
| **React Dashboard** | Vite + React + Recharts | Focus timeline, emotion radar, Whoop card, logs | Optional |

### 2. Python FastAPI Backend (`localhost:8420`)

The backend is the **central brain** — all interfaces are thin clients that call it.

| Subsystem | Key Files | Purpose |
|-----------|-----------|---------|
| **API Routes** | `api/screen.py`, `api/chat.py`, `api/whoop.py`, `api/insights.py` | REST endpoints |
| **Activity Classifier** | `services/activity_classifier.py` | 4-layer app/URL/title classification |
| **ADHD Metrics Engine** | `services/adhd_metrics.py` | Rolling window behavioral metrics |
| **JITAI Engine** | `services/jitai_engine.py` | Barkley's 5 EF-domain intervention rules |
| **XAI Explainer** | `services/xai_explainer.py` | Concept Bottleneck + counterfactual explanations |
| **SenticNet Pipeline** | `services/senticnet_pipeline.py` | 4-tier 13-API orchestration |
| **Whoop Service** | `services/whoop_service.py` | OAuth + recovery/sleep data processing |
| **MLX Inference** | `services/mlx_inference.py` | Llama 3.2 3B on Apple Silicon |
| **Chat Processor** | `services/chat_processor.py` | Full pipeline for venting messages |
| **Memory Service** | `services/memory_service.py` | Mem0 + PostgreSQL pattern storage |

### 3. Data Layer

| Store | Technology | Contents |
|-------|-----------|----------|
| **PostgreSQL + pgvector** | Docker (`pgvector/pgvector:pg16`) | Activities, SenticNet analyses, interventions, Whoop data, conversations, vector embeddings |
| **SQLite** | Local file | Offline activity buffer, app category cache, recent metrics |

### 4. External APIs

| API | Purpose | Auth |
|-----|---------|------|
| SenticNet Cloud | 13 affective computing endpoints | API keys (IP-locked) |
| Whoop API v2 | Recovery, sleep, cycles | OAuth 2.0 |
| Claude Sonnet | Complex coaching queries | API key |
| GPT-4o-mini | Frequent tasks, embeddings | API key |

---

## Data Flow — Screen Monitoring (Hot Path)

```
Swift App (2s polling)
    │
    ▼ POST /screen/activity (<100ms target)
    │
    ├── 1. Activity Classifier (rule-based, <5ms)
    │       L1: App name → L2: URL domain → L3: Title keywords → L4: MLX fallback
    │
    ├── 2. ADHD Metrics Engine (in-memory, <1ms)
    │       Context switch rate, focus score, distraction ratio, streak
    │
    ├── 3. JITAI Engine (rule engine, <2ms)
    │       Check Barkley's 5 EF domains → generate intervention or null
    │
    └── 4. Background Tasks (async, non-blocking)
            ├── Persist to PostgreSQL
            └── Enrich with SenticNet (if intervention needs it)
```

## Data Flow — Chat/Venting (Warm Path)

```
OpenClaw / Dashboard
    │
    ▼ POST /chat/message (<3s target)
    │
    ├── Tier 1: Safety check (depression + toxicity + intensity)
    │       ↳ If CRITICAL → emergency response + crisis resources
    │
    ├── Tier 2: Core emotional (emotion + polarity + subjectivity + sarcasm)
    │
    ├── Tier 3: ADHD signals (engagement + wellbeing + concepts + aspects)
    │
    ├── Tier 4: Deep analysis (personality + ensemble) — if needed
    │
    ├── LLM Generation (MLX Llama 3B with SenticNet context injection)
    │
    └── Memory Storage (Mem0 + PostgreSQL)
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **macOS** | 14+ (Sonoma) | 15+ (Sequoia) |
| **Chip** | Apple M1 | Apple M3/M4 |
| **RAM** | 8GB | 16GB (for MLX models) |
| **Python** | 3.11+ | 3.12+ |
| **Node.js** | 22+ (OpenClaw only) | — |
| **PostgreSQL** | 16 + pgvector | via Docker |
| **Xcode** | 15+ | 16+ |

---

## Repository Structure

```
adhd-second-brain/
├── backend/                    # Python FastAPI backend
│   ├── api/                    # REST API routes
│   ├── services/               # Business logic (SenticNet, JITAI, XAI, etc.)
│   ├── models/                 # Pydantic data models
│   ├── db/                     # Database layer (PostgreSQL + Alembic)
│   ├── knowledge/              # Static knowledge bases (JSON)
│   └── tests/                  # pytest unit tests
├── swift-app/                  # Native macOS menu bar app
│   └── ADHDSecondBrain/        # Swift source
├── openclaw-skills/            # OpenClaw custom skills (Telegram/WhatsApp)
├── dashboard/                  # Optional React web dashboard
├── scripts/                    # Setup, start, seed, validate scripts
├── docs/                       # This documentation folder
├── docker-compose.yml          # PostgreSQL + pgvector
└── .env.example                # Environment variable template
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Phase 1: Python Backend](PHASE_1_PYTHON_BACKEND.md) | Foundation — FastAPI, routes, config |
| [Phase 2: Swift Menu Bar](PHASE_2_SWIFT_MENU_BAR.md) | Native macOS screen monitor + UI |
| [Phase 3: SenticNet Pipeline](PHASE_3_SENTICNET_PIPELINE.md) | 13-API affective computing |
| [Phase 4: XAI & JITAI Engine](PHASE_4_XAI_JITAI_ENGINE.md) | Explainable interventions |
| [Phase 5: Whoop Integration](PHASE_5_WHOOP_INTEGRATION.md) | Physiological data |
| [Phase 6: Memory System](PHASE_6_MEMORY_SYSTEM.md) | Mem0 + pattern storage |
| [Phase 7: On-Device LLM](PHASE_7_ON_DEVICE_LLM.md) | Apple MLX inference |
| [Phase 8: OpenClaw](PHASE_8_OPENCLAW.md) | Telegram/WhatsApp chat interface |
| [Phase 9: Frontend Dashboard](PHASE_9_FRONTEND_DASHBOARD.md) | React web dashboard |
| [Data Models](DATA_MODELS.md) | Database schemas + Pydantic models |
| [API Contracts](API_CONTRACTS.md) | Full endpoint reference |
| [Testing Strategy](TESTING_STRATEGY.md) | Unit + integration testing |
| [Project Timeline](PROJECT_TIMELINE.md) | Build order + critical path |

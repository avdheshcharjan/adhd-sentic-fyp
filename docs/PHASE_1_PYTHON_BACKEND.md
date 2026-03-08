# Phase 1: Python Backend (Core Engine)

> **Priority**: 🔴 BUILD THIS FIRST — everything depends on it  
> **Timeline**: Week 1–2  
> **Dependencies**: Docker (PostgreSQL), Python 3.11+

---

## Overview

The Python FastAPI backend is the central brain of the ADHD Second Brain system. All interfaces (Swift app, OpenClaw, Dashboard) are thin clients that call it via REST. This phase establishes the foundation: project setup, core API routes, in-memory metrics, and the activity classifier.

---

## Objectives

1. Set up the repository, Docker services, and environment configuration
2. Create the FastAPI application skeleton with all route stubs
3. Implement the `POST /screen/activity` endpoint with in-memory metrics
4. Implement the 4-layer activity classifier (Layers 1–3, no ML)
5. Implement the ADHD Metrics Engine (rolling window)
6. Validate with manual `curl` testing

---

## Key Files to Create

### Project Configuration

| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL + pgvector container |
| `.env.example` | Environment variable template |
| `.gitignore` | Python + macOS + IDE ignores |
| `backend/pyproject.toml` | Python project metadata |
| `backend/requirements.txt` | Python dependencies |

### Application Core

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry point, middleware, router includes |
| `backend/config.py` | `pydantic-settings` based configuration from `.env` |

### API Routes (Stubs)

| File | Endpoint | Purpose |
|------|----------|---------|
| `backend/api/screen.py` | `POST /screen/activity` | **Primary endpoint** — called every 2s by Swift app |
| `backend/api/chat.py` | `POST /chat/message` | Venting/chat processing (stub) |
| `backend/api/whoop.py` | `GET /whoop/*` | Whoop OAuth + morning briefing (stub) |
| `backend/api/insights.py` | `GET /insights/*` | Daily/weekly insights (stub) |
| `backend/api/interventions.py` | `GET/POST /interventions/*` | Intervention delivery + response (stub) |
| `backend/api/health.py` | `GET /health` | Health check |

### Business Logic

| File | Purpose |
|------|---------|
| `backend/services/activity_classifier.py` | 4-layer activity classifier (app → URL → title → MLX fallback) |
| `backend/services/adhd_metrics.py` | Rolling window ADHD metrics (in-memory `deque`) |

### Knowledge Bases

| File | Purpose |
|------|---------|
| `backend/knowledge/app_categories.json` | App name → category mapping (~40 entries) |
| `backend/knowledge/url_categories.json` | Domain → category mapping (~30 entries) |

---

## Implementation Details

### 1. FastAPI Application Setup (`main.py`)

```python
# Key design decisions:
# - Use lifespan handler for startup/shutdown (init_db, init_memory)
# - CORS middleware with allow_origins=["*"] (lock down in production)
# - All routes mounted with prefix (/screen, /chat, /whoop, etc.)
# - Port 8420 (unique to avoid conflicts)
```

**Configuration** (`config.py`):
- Uses `pydantic_settings.BaseSettings` for type-safe env var management
- All SenticNet API keys, Whoop credentials, LLM keys, DB URLs
- Default values for local development
- `INTERVENTION_COOLDOWN_SECONDS = 300` (5 minutes between interventions)

### 2. Screen Activity Endpoint (`POST /screen/activity`)

This is the **hottest path** in the system — called every 2 seconds.

**Latency target**: < 100ms response

**Processing pipeline**:
1. **Classify activity** — rule-based, <5ms
2. **Update rolling metrics** — in-memory, <1ms
3. **Check intervention need** — rule engine, <2ms
4. **Background persistence** — async, non-blocking
5. **SenticNet enrichment** — async background if intervention requires it

**Request model** (`ScreenActivityInput`):
```python
class ScreenActivityInput(BaseModel):
    app_name: str           # e.g., "Google Chrome"
    window_title: str       # e.g., "YouTube - Funny Cats"
    url: str | None = None  # e.g., "https://youtube.com/watch?v=..."
    is_idle: bool = False   # True if keyboard/mouse idle >60s
    timestamp: datetime = Field(default_factory=datetime.now)
```

**Response model** (`ScreenActivityResponse`):
```python
class ScreenActivityResponse(BaseModel):
    category: str           # e.g., "entertainment"
    metrics: dict           # Current ADHD metrics snapshot
    intervention: Intervention | None  # Pending intervention or null
```

### 3. Activity Classifier (4-Layer System)

| Layer | Coverage | Latency | Method |
|-------|----------|---------|--------|
| **L1**: App name | ~70% | <1ms | Dictionary lookup (`app_categories.json`) |
| **L2**: URL domain | ~20% | <1ms | Domain extraction + lookup (`url_categories.json`) |
| **L3**: Title keywords | ~8% | <2ms | Keyword matching in window title |
| **L4**: MLX fallback | ~2% | ~200ms | On-device LLM classification (async) |

**Output categories**: `development`, `writing`, `research`, `communication`, `social_media`, `entertainment`, `news`, `shopping`, `productivity`, `design`, `browser`, `system`, `other`

### 4. ADHD Metrics Engine

**In-memory rolling window** using `collections.deque`:
- `activity_log` — last 30 min at 2s intervals (maxlen=900)
- `app_switches` — last 5 min of switches (maxlen=150)

**Computed metrics**:

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `context_switch_rate_5min` | App switches per 5 min | >12 = high distraction |
| `focus_score` | % time in 15+ min productive sessions | <30% = intervention |
| `distraction_ratio` | Time in distracting vs productive apps | 0–1 scale |
| `current_streak_minutes` | Minutes on current app | — |
| `hyperfocus_detected` | 3+ hrs on single non-priority task | 180 min |
| `behavioral_state` | Derived state label | See below |

**Behavioral states**: `focused` | `multitasking` | `distracted` | `hyperfocused` | `idle`

---

## Docker Setup

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: adhd_brain
      POSTGRES_USER: adhd
      POSTGRES_PASSWORD: adhd
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
```

---

## Verification Checklist

- [ ] `docker compose up -d` starts PostgreSQL successfully
- [ ] `uvicorn main:app --port 8420 --reload` starts without errors
- [ ] `GET /health` returns `200 OK`
- [ ] `POST /screen/activity` accepts input and returns classification + metrics
- [ ] Activity classifier correctly categorizes known apps (VSCode → development)
- [ ] Activity classifier correctly categorizes known URLs (github.com → development)
- [ ] Metrics engine tracks context switch rate accurately
- [ ] Behavioral state transitions work (idle → focused → distracted)
- [ ] Response time < 100ms for `/screen/activity`

### Test Commands

```bash
# Health check
curl http://localhost:8420/health

# Screen activity report
curl -X POST http://localhost:8420/screen/activity \
  -H "Content-Type: application/json" \
  -d '{"app_name":"Google Chrome","window_title":"YouTube - Funny Cats","url":"https://youtube.com/watch?v=abc"}'

# Productive activity
curl -X POST http://localhost:8420/screen/activity \
  -H "Content-Type: application/json" \
  -d '{"app_name":"Visual Studio Code","window_title":"main.py — adhd-brain","url":null}'
```

---

## Dependencies

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
httpx==0.28.*
pydantic==2.*
pydantic-settings==2.*
asyncpg==0.30.*
sqlalchemy[asyncio]==2.*
alembic==1.14.*
pgvector==0.3.*
python-dotenv==1.*
```

---

## Next Phase

→ [Phase 2: Swift Menu Bar App](PHASE_2_SWIFT_MENU_BAR.md) (can start in parallel after routes are stable)  
→ [Phase 3: SenticNet Pipeline](PHASE_3_SENTICNET_PIPELINE.md) (depends on this phase)

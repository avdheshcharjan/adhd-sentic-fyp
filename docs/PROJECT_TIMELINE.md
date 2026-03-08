# Project Timeline & Build Order

> 8-week critical path with ~40 numbered tasks across 7 build phases.

---

## Timeline Overview

```
Week 1-2  ███████████████░░░░░░░░░░░░░░░░  Phase 1: Foundation (Backend)
Week 2-3  ░░░░░░░████████████░░░░░░░░░░░░  Phase 2: SenticNet Pipeline
Week 3-4  ░░░░░░░░░░░░████████████░░░░░░░  Phase 3: JITAI + XAI
Week 4-5  ░░░░░░░░░░░░░░░░████████████░░░  Phase 4: Swift Menu Bar App
Week 5-6  ░░░░░░░░░░░░░░░░░░░░████████░░░  Phase 5: Whoop + Memory
Week 6-7  ░░░░░░░░░░░░░░░░░░░░░░░████████  Phase 6: MLX + OpenClaw
Week 7-8  ░░░░░░░░░░░░░░░░░░░░░░░░░██████  Phase 7: Dashboard + Polish
```

---

## Phase 1: Foundation (Week 1–2)

> **Goal**: Backend skeleton that accepts screen data and returns classifications + metrics

| # | Task | Depends On |
|---|------|-----------|
| 1 | Set up repo, `docker-compose.yml`, `.env.example`, `.gitignore` | — |
| 2 | Create FastAPI skeleton with all route stubs | 1 |
| 3 | Implement `POST /screen/activity` with in-memory metrics | 2 |
| 4 | Implement `activity_classifier.py` (Layers 1-3, no ML) | 2 |
| 5 | Implement `adhd_metrics.py` (MetricsEngine) | 2 |
| 6 | Test with `curl` commands | 3, 4, 5 |

### Milestone: Backend responds to screen activity reports with correct classifications

---

## Phase 2: SenticNet Pipeline (Week 2–3)

> **Goal**: Full 13-API affective computing pipeline

| # | Task | Depends On |
|---|------|-----------|
| 7 | Implement `senticnet_client.py` | 2 |
| 8 | Write `test_senticnet_keys.py` to validate all 13 API keys | 7 |
| 9 | Implement `senticnet_pipeline.py` (full + lightweight + safety) | 7 |
| 10 | Implement `POST /chat/message` with full pipeline | 9 |
| 11 | Test chat endpoint with emotional text | 10 |

### Milestone: Chat endpoint processes emotional text through 13 SenticNet APIs

---

## Phase 3: JITAI + XAI (Week 3–4)

> **Goal**: Intelligent interventions with explainable justifications

| # | Task | Depends On |
|---|------|-----------|
| 12 | Implement `jitai_engine.py` with all 4 intervention rules | 5 |
| 13 | Implement `xai_explainer.py` | 9, 12 |
| 14 | Wire JITAI into `POST /screen/activity` (return interventions) | 12, 3 |
| 15 | Write comprehensive unit tests for JITAI rules | 12 |

### Milestone: Screen activity endpoint triggers appropriate interventions with explanations

---

## Phase 4: Swift Menu Bar App (Week 4–5)

> **Goal**: Native macOS app capturing screen state and showing interventions

| # | Task | Depends On |
|---|------|-----------|
| 16 | Create Xcode project with `LSUIElement=true` | — |
| 17 | Implement `ScreenMonitor.swift` (NSWorkspace + CGWindowList) | 16 |
| 18 | Implement `BrowserMonitor.swift` (AppleScript) | 16 |
| 19 | Implement `IdleMonitor.swift` | 16 |
| 20 | Implement `BackendClient.swift` (HTTP to localhost:8420) | 16, 3 |
| 21 | Implement `InterventionPopup.swift` | 16 |
| 22 | Implement `OnboardingView.swift` (permissions wizard) | 16 |
| 23 | Test end-to-end: Swift → Backend → Intervention | 17-22 |

### Milestone: Swift captures screen → Backend processes → Intervention popup appears

---

## Phase 5: Whoop + Memory (Week 5–6)

> **Goal**: Physiological data integration + long-term pattern memory

| # | Task | Depends On |
|---|------|-----------|
| 24 | Register Whoop developer app, get client ID/secret | — |
| 25 | Implement Whoop OAuth flow | 2 |
| 26 | Implement `whoop_service.py` + morning briefing | 25 |
| 27 | Set up Mem0 with PostgreSQL/pgvector | 1 |
| 28 | Implement `memory_service.py` | 27 |
| 29 | Wire memory into chat processor (context injection) | 28, 10 |

### Milestone: Morning briefing generated from Whoop data; chat uses memory context

---

## Phase 6: MLX + OpenClaw (Week 6–7)

> **Goal**: On-device LLM + messaging gateway

| # | Task | Depends On |
|---|------|-----------|
| 30 | Install MLX, download Llama 3.2 3B | — |
| 31 | Implement `mlx_inference.py` | 30 |
| 32 | Wire MLX into chat_processor for response generation | 31, 10 |
| 33 | Install OpenClaw, create custom skills | 10 |
| 34 | Test venting flow: Telegram → OpenClaw → Backend → Response | 33, 32 |
| 35 | Configure HEARTBEAT.md for morning briefings | 33, 26 |

### Milestone: End-to-end venting via Telegram with on-device LLM responses

---

## Phase 7: Dashboard + Polish (Week 7–8)

> **Goal**: Visual dashboard for FYP demo + final polish

| # | Task | Depends On |
|---|------|-----------|
| 36 | Build React dashboard (FocusTimeline, EmotionRadar, WhoopCard) | 2 |
| 37 | Implement `GET /insights/dashboard` endpoint | 5, 9, 12 |
| 38 | End-to-end testing of all flows | All |
| 39 | Performance optimization (response times, memory usage) | 38 |
| 40 | Demo preparation | 38, 39 |

### Milestone: Polished system ready for FYP demonstration

---

## Critical Path

```
Tasks 1-6 (Backend) → Tasks 7-11 (SenticNet) → Tasks 12-15 (JITAI/XAI) → Task 23 (E2E)
                                                                            ↑
                                                    Tasks 16-22 (Swift) ────┘
```

The Swift app (Phase 4) can start **in parallel** with Phases 2-3 once the backend route stubs are stable.

---

## Important Decision Points

> [!CAUTION]
> **SenticNet API keys expire after ~1 month** and are IP-locked. Test them in Week 2 and request new ones early if needed.

> [!WARNING]
> **Swift app must be distributed outside Mac App Store** due to Screen Recording + Apple Events entitlements.

> [!WARNING]
> **macOS Sequoia re-prompts** for Accessibility/Screen Recording monthly. Build re-auth UX.

> [!IMPORTANT]
> **Log everything for FYP report**: Every SenticNet API call and JITAI decision must have timestamps for the results chapter.

> [!IMPORTANT]
> **Safety is non-negotiable**: Depression/toxicity check runs FIRST in every pipeline.

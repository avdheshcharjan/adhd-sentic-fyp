# Phase 6: Memory System

> **Timeline**: Week 5–6  
> **Dependencies**: Phase 1 (backend + PostgreSQL), Phase 3 (SenticNet)

---

## Overview

A dual-layer memory system that provides long-term pattern tracking and personalized context for LLM responses. Layer 1 handles conversational memory via Mem0; Layer 2 handles behavioral pattern storage via PostgreSQL + pgvector.

---

## Dual-Layer Architecture

```
┌──────────────────────────────────────────┐
│           MEMORY SERVICE                  │
│                                          │
│  ┌────────────────────┐  ┌─────────────┐│
│  │  Layer 1: Mem0      │  │  Layer 2:   ││
│  │  (Conversational)   │  │  PostgreSQL ││
│  │                     │  │  + pgvector ││
│  │  • User preferences │  │             ││
│  │  • Emotional patterns│  │  • Activities││
│  │  • Intervention resp │  │  • SenticNet ││
│  │  • Chat context      │  │  • Interventn││
│  │                     │  │  • Whoop data ││
│  │  Powered by:        │  │  • Trends    ││
│  │  GPT-4o-mini (LLM)  │  │             ││
│  │  text-embedding-3   │  │             ││
│  │  small (embeddings) │  │             ││
│  └────────────────────┘  └─────────────┘│
└──────────────────────────────────────────┘
```

---

## Layer 1: Mem0 (Conversational Memory)

### Purpose
- Stores user preferences, emotional patterns, and conversational context
- Used for personalizing LLM responses
- Enables context retrieval across chat sessions

### Configuration
```python
{
    "llm": {"provider": "openai", "model": "gpt-4o-mini"},
    "embedder": {"provider": "openai", "model": "text-embedding-3-small"},
    "vector_store": {"provider": "pgvector", "collection": "adhd_memories"}
}
```

### Key Operations

| Method | Purpose | Example |
|--------|---------|---------|
| `add_conversation_memory()` | Store chat context after vent session | User said "mornings are hardest" |
| `add_pattern_memory()` | Store detected behavioral patterns | "User procrastinates on writing tasks" |
| `search_relevant_context()` | Retrieve context for LLM injection | Query: "frustration with deadlines" |
| `get_intervention_history()` | Past intervention responses | Which interventions worked? |

---

## Layer 2: PostgreSQL (Behavioral Patterns)

### Purpose
- Time-series storage of all screen activities, analyses, and outcomes
- Structured queries for trend analysis and weekly reviews
- Vector embeddings via pgvector for semantic search

### Tables Used
- `activities` — screen activity log (partitioned by date)
- `senticnet_analyses` — emotion analysis results
- `interventions` — intervention history + user responses
- `whoop_data` — daily Whoop snapshots
- `conversations` + `messages` — chat history with SenticNet analysis

---

## Integration Points

| Consumer | How Memory is Used |
|----------|-------------------|
| **Chat Processor** | Retrieves relevant memories for LLM context injection |
| **JITAI Engine** | Checks intervention history to avoid repeating ineffective ones |
| **Morning Briefing** | Includes patterns from recent days |
| **Weekly Review** | Aggregates intervention effectiveness trends |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/services/memory_service.py` | Mem0 wrapper + pattern storage |
| `backend/db/repositories/pattern_repo.py` | PostgreSQL pattern queries |

---

## Verification Checklist

- [ ] Mem0 initializes with pgvector backend
- [ ] Conversation memories stored after chat sessions
- [ ] Pattern memories stored from behavioral detection
- [ ] Search retrieves semantically relevant context
- [ ] Intervention history correctly filters by type
- [ ] Memory context injected into LLM prompts

---

## Next Phase

→ [Phase 7: On-Device LLM](PHASE_7_ON_DEVICE_LLM.md)

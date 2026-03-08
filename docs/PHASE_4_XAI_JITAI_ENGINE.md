# Phase 4: Explainable AI & JITAI Engine

> **Timeline**: Week 3–4  
> **Dependencies**: Phase 1 (metrics engine), Phase 3 (SenticNet pipeline)

---

## Overview

This phase implements the intelligence layer: the JITAI (Just-in-Time Adaptive Intervention) decision engine based on Barkley's 5 Executive Function deficit domains, and the XAI (Explainable AI) engine using a Concept Bottleneck architecture for transparent, human-readable explanations.

---

## Barkley's 5 Executive Function Domains

| # | EF Domain | ADHD Deficit | System Detection |
|---|-----------|-------------|-----------------|
| 1 | **Self-management to time** | Losing track of time, hyperfocusing on wrong tasks | Hyperfocus detection (3+ hrs on single task) |
| 2 | **Self-organization** | Trouble starting tasks, disorganized approach | Sustained disengagement, low task initiation |
| 3 | **Self-restraint (inhibition)** | Can't resist distractions, impulsive tab switching | High context switch rate + distraction ratio |
| 4 | **Self-motivation** | Avoidance, procrastination, can't sustain effort | Sustained time on distracting apps, low focus score |
| 5 | **Self-regulation of emotion** | Emotional flooding, frustration spirals | SenticNet emotional dysregulation signals |

---

## JITAI Engine — Intervention Rules

### Decision Flow

```
Metrics Input
    │
    ├── DND mode? ──────────────── → No intervention
    ├── Within cooldown? ───────── → No intervention
    ├── User focused? ──────────── → No intervention
    │
    ├── Rule 1: Distraction spiral?
    │   (switches > 12/5min AND distraction > 50%)
    │   → Self-restraint intervention
    │
    ├── Rule 2: Sustained disengagement?
    │   (distracted > 20min AND distraction > 70%)
    │   → Self-motivation intervention
    │
    ├── Rule 3: Hyperfocus on wrong task?
    │   (streak > 3 hours)
    │   → Self-management-to-time intervention
    │
    └── Rule 4: Emotional escalation?
        (SenticNet emotional_dysregulation = true)
        → Self-regulation-of-emotion intervention
```

### Intervention Rules Detail

| Rule | Trigger | EF Domain | Acknowledgment | Suggestion | Actions |
|------|---------|-----------|----------------|------------|---------|
| Distraction Spiral | >12 switches/5min + >50% distraction | Self-restraint | "Looks like things are scattered right now — that's okay." | "A 2-minute reset could help you refocus." | 🫁 Breathing / 🎯 Pick task / ☕ Break |
| Sustained Disengagement | >20min distracted + >70% ratio | Self-motivation | "It's been a while since your last focused stretch." | "What's the smallest step you could take?" | 🪜 5-min task / 👥 Body double / 🎁 Set reward |
| Hyperfocus Check | >3hrs on single task | Self-mgmt to time | "You've been deeply focused for 3+ hours!" | "Is this the most important thing right now?" | ✅ Continue / 🔄 Switch / ⏰ Timer |
| Emotional Escalation | SenticNet `emotional_dysregulation` | Self-regulation | "Things seem intense right now. That's valid." | "Would any of these help?" | 💬 Vent / 🌿 Grounding / 🚶 Walk |

### Adaptive Cooldown System

- Default cooldown: **5 minutes** between interventions
- After 3+ consecutive dismissals: cooldown increases by **1.5×** (up to 30 min max)
- After user engages with an intervention: cooldown resets to 5 min

### Hard Blocks (Never Interrupt)
- User is in `focused` behavioral state
- DND mode is active
- Within cooldown period
- During detected meetings (Zoom, Teams, Meet active)

---

## XAI Explanation Engine — Concept Bottleneck Model

### Architecture
```
Raw Data → Feature Extraction → SenticNet Concept Activations → Behavioral Prediction → Explanation
```

### Three Explanation Types

| Type | Question | Example |
|------|----------|---------|
| **WHAT** | What happened? | "You've switched apps 15 times in the last 5 minutes, with 65% of time on non-work apps." |
| **WHY** | Why is this happening? | "SenticNet detected frustration (0.82) and overwhelm (0.71). This maps to EF challenges with focus." |
| **HOW** | What would improve things? | "A 2-minute breathing reset can reduce context switching by ~40%." (Counterfactual) |

### Explanation Output Structure
```python
{
    "what": "You've switched apps 15 times...",
    "why": "Emotional analysis detected frustration...",
    "how": "Research shows a 2-minute breathing reset...",
    "concepts": ["frustration", "overwhelm"],    # SenticNet concepts
    "hourglass_state": {                         # 4 Hourglass dimensions
        "pleasantness": -0.6,
        "attention": -0.3,
        "sensitivity": 0.8,
        "aptitude": -0.4
    },
    "confidence": 0.85
}
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/services/jitai_engine.py` | JITAI decision engine with 4 intervention rules |
| `backend/services/xai_explainer.py` | Concept Bottleneck explanation generator |
| `backend/models/intervention.py` | Intervention + InterventionAction Pydantic models |
| `backend/models/explanation.py` | Explanation output model |
| `backend/knowledge/adhd_interventions.json` | Evidence-based intervention library |
| `backend/knowledge/barkley_ef_model.json` | Barkley's 5 EF domain definitions |

---

## Intervention Model

```python
class Intervention(BaseModel):
    type: str                        # "distraction_spiral", "hyperfocus_check", etc.
    ef_domain: str                   # Barkley EF domain
    acknowledgment: str              # Validate before suggesting
    suggestion: str                  # Short, actionable
    actions: list[InterventionAction]  # Max 2–3 choices
    requires_senticnet: bool         # Whether to enrich with SenticNet

class InterventionAction(BaseModel):
    id: str         # "breathe", "task_pick", "break"
    emoji: str      # "🫁", "🎯", "☕"
    label: str      # "Breathing exercise", "Pick one task", "Take a break"
```

---

## Integration with Screen Activity Endpoint

The JITAI engine is wired into `POST /screen/activity`:

1. Activity classifier runs → category
2. Metrics engine updates → ADHDMetrics
3. **JITAI evaluates** → Intervention or `None`
4. If intervention has `requires_senticnet=True` → background SenticNet enrichment
5. XAI generates explanation attached to intervention
6. Response includes intervention (if any)

---

## FYP Logging Requirement

> Every JITAI decision should be logged with timestamps. This provides the evaluation data needed for the FYP report's results chapter.

Log format:
```json
{
    "timestamp": "2026-03-08T12:00:00Z",
    "metrics": { ... },
    "intervention_type": "distraction_spiral",
    "ef_domain": "self_restraint",
    "user_response": "breathe",
    "dismissed": false,
    "explanation": { ... }
}
```

---

## Verification Checklist

- [ ] Distraction spiral triggers intervention (>12 switches + >50% distraction)
- [ ] Focused state blocks all interventions
- [ ] Cooldown prevents spam (no intervention within 5 min of last)
- [ ] Adaptive cooldown increases after 3+ dismissals
- [ ] Hyperfocus detected after 3+ hours on single task
- [ ] Emotional escalation triggers SenticNet-enriched intervention
- [ ] XAI generates WHAT/WHY/HOW explanations
- [ ] Counterfactual explanations reference evidence-based research
- [ ] Intervention response tracking works (record_response)

---

## Next Phase

→ [Phase 5: Whoop Integration](PHASE_5_WHOOP_INTEGRATION.md)

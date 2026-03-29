# SenticNet API vs SetFit Model: Usage Strategy

> Research document — how the two emotion systems should work together across the ADHD Second Brain product.

---

## 1. Current State: What Each System Does

### SenticNet API (13 endpoints, external cloud service)

| API | What It Returns | Current Usage | Path |
|-----|----------------|---------------|------|
| **emotion** | `"fear (99.7%) & annoyance (50.0%)"` | Overwritten by SetFit in both pipelines | Lightweight + Full |
| **polarity** | `"POSITIVE" / "NEGATIVE" / "NEUTRAL"` | LLM prompt context, vent escalation tracking | Full only |
| **intensity** | Float score (-100 to 100) | Safety gate, thinking-mode toggle, `is_overwhelmed` / `is_frustrated` / `emotional_dysregulation` flags | Lightweight + Full |
| **depression** | Percentage (0-100) | Safety level computation (critical/high/moderate/normal) | Full + Safety |
| **toxicity** | Percentage (0-100) | Safety level computation, self-directed negativity detection | Full + Safety |
| **engagement** | Percentage (-100 to 100) | `is_disengaged` flag, LLM context | Lightweight + Full |
| **wellbeing** | Percentage (-100 to 100) | `is_overwhelmed` flag, LLM context | Full only |
| **subjectivity** | String | `is_subjective` flag (stored, not forwarded) | Full only |
| **sarcasm** | String | `sarcasm_detected` flag (stored, not forwarded) | Full only |
| **personality** | `"ENTJ (O↑C↑E↑A↓N↓)"` | Big 5 profile (stored, not used downstream) | Full only |
| **concepts** | Concept list | Top 5 injected into LLM prompt | Full only |
| **aspects** | Aspect string | Stored, not forwarded | Full only |
| **ensemble** | 14-field dict | Hourglass dimensions (introspection/temper/attitude/sensitivity), backfills tier1/3 scores | Full only |

**Strengths**: Dimensional scoring (not just labels), safety detection, engagement/wellbeing signals, personality, concept extraction, ensemble fusion.

**Weaknesses**: 28% accuracy on ADHD emotion classification, requires internet, costs per API call, adds latency (3 APIs ~500ms, 13 APIs ~2-3s).

---

### SetFit Model (trained, on-device, 86% accuracy)

| Property | Value |
|----------|-------|
| Architecture | all-mpnet-base-v2 (fine-tuned Phase 1, CoSENTLoss) → LogisticRegression head (Phase 2) |
| Categories | `joyful`, `focused`, `frustrated`, `anxious`, `disengaged`, `overwhelmed` |
| Accuracy | **86%** (50-sentence test set, 210 training sentences) |
| Latency | <50ms on CPU (embedding + classify) |
| Size | 418 MB on disk |
| Internet | Not required |

**Strengths**: ADHD-specific categories, high accuracy, fast, works offline, no API cost.

**Weaknesses**: Only produces a label + confidence (no dimensional scores), no safety detection, no engagement/wellbeing signals, no concept extraction.

---

## 2. Wiring Issues (Fixed)

### Issue 1: Emotion Radar shows all zeros — FIXED

The dashboard's Emotion Radar reads PASE scores from `SenticAnalysis.emotion_profile`:

```python
# notch.py reads these keys:
pleasantness += profile.get("pleasantness", 0.0)   # ← KEY DOESN'T EXIST
attention    += profile.get("attention", 0.0)       # ← KEY DOESN'T EXIST
sensitivity  += profile.get("sensitivity", 0.0)     # ✓ matches
aptitude     += profile.get("aptitude", 0.0)        # ← KEY DOESN'T EXIST
```

The stored keys from `EmotionProfile.model_dump()` are: `introspection`, `temper`, `attitude`, `sensitivity`.
Three out of four keys don't match → radar shows 0.0 for 3/4 dimensions.

Additionally, in the **lightweight pipeline** (used for screen activity), Hourglass dimensions are **never populated** — they're only filled by the Tier 4 ensemble in the full pipeline. So even fixing the key names won't help for screen data.

### Issue 2: SetFit confidence is discarded — FIXED

Both call sites capture `setfit_confidence` but immediately discard it:
```python
setfit_label, setfit_confidence = setfit_classifier.predict(text)
# setfit_confidence is never stored, displayed, or used for gating
```

### Issue 3: JITAI Rule 4 (emotional escalation) can never fire — FIXED

`screen.py` calls `jitai_engine.evaluate(metrics)` without passing `emotion_context`.
Rule 4 checks `emotion_context.get("emotional_dysregulation")` — always `None`.
SetFit's `overwhelmed` → `emotional_dysregulation` mapping exists but is never wired to JITAI.

### Issue 4: SetFit `primary_adhd_state` is stored but not consumed by dashboard — FIXED

The SetFit-derived `primary_adhd_state` is saved in `SenticAnalysis.emotion_profile` (inside the `primary_emotion` field), but the dashboard reads PASE Hourglass scores, not the ADHD state label. The SetFit label is only consumed by:
- Chat LLM prompt (via `_build_senticnet_context()`)
- Vent LLM prompt (via `emotion_context` string)
- Brain dump Mem0 storage

### Issue 5: `TransitionDetector` is instantiated but never called — DEFERRED

The JITAI engine creates a `TransitionDetector` but never calls its methods — `should_suppress_intervention()` is dead code. Left as-is since Gate 1 hyperfocus protection serves a similar purpose.

---

## 3. Recommended Strategy: How to Use Each System

### Principle: SetFit for WHAT emotion, SenticNet for HOW MUCH and WHY

| Dimension | Best Source | Rationale |
|-----------|-----------|-----------|
| **Primary emotion label** (joyful/focused/frustrated/anxious/disengaged/overwhelmed) | **SetFit** | 86% accuracy vs SenticNet's 28%. ADHD-specific categories designed for this product. |
| **Emotion confidence/certainty** | **SetFit** | Confidence score should gate low-certainty predictions (don't intervene if < 0.6). |
| **Dimensional emotion scoring** (pleasantness/attention/sensitivity/aptitude) | **SetFit-derived** | Map SetFit labels → fixed PASE profiles (see Section 4). More reliable than SenticNet Hourglass on short text. |
| **Safety detection** (depression, toxicity, crisis) | **SenticNet** | SetFit has no safety capability. This is non-negotiable — safety MUST use SenticNet's dedicated APIs. |
| **Engagement level** | **SenticNet** | SetFit doesn't measure engagement directly. `disengaged` label is binary; SenticNet's -100 to +100 scale is richer. |
| **Wellbeing level** | **SenticNet** | No SetFit equivalent. Important for overwhelm detection in combination with intensity. |
| **Intensity/arousal** | **SenticNet** | Continuous scale critical for safety thresholds and thinking-mode decisions. |
| **Concept extraction** | **SenticNet** | SetFit produces no semantic concepts. Needed for XAI explanations and LLM context. |
| **Personality profiling** | **SenticNet** | SetFit has no personality capability. Useful for long-term coaching personalization. |
| **Polarity tracking** | **SenticNet** | Continuous polarity score needed for vent session escalation detection. |
| **Intervention triggering** | **SetFit + Behavioral metrics** | SetFit's `overwhelmed`/`frustrated`/`anxious` should directly activate JITAI Rule 4. Currently unwired. |

---

## 4. Recommended Wiring: SetFit → Emotion Radar

Map each SetFit label to a canonical PASE profile for the radar visualization. These profiles represent the typical emotional geometry of each ADHD state:

```python
SETFIT_TO_PASE: dict[str, dict[str, float]] = {
    "joyful":      {"pleasantness": 0.85, "attention": 0.70, "sensitivity": 0.30, "aptitude": 0.75},
    "focused":     {"pleasantness": 0.60, "attention": 0.90, "sensitivity": 0.20, "aptitude": 0.80},
    "frustrated":  {"pleasantness": 0.15, "attention": 0.40, "sensitivity": 0.80, "aptitude": 0.30},
    "anxious":     {"pleasantness": 0.20, "attention": 0.55, "sensitivity": 0.90, "aptitude": 0.25},
    "disengaged":  {"pleasantness": 0.35, "attention": 0.15, "sensitivity": 0.25, "aptitude": 0.20},
    "overwhelmed": {"pleasantness": 0.10, "attention": 0.30, "sensitivity": 0.85, "aptitude": 0.15},
}
```

**Why this works**: The radar should show the *user's emotional shape*, not raw API numbers. SetFit at 86% accuracy gives us a reliable label, and the PASE mapping turns that into an intuitive visualization.

**Blending with confidence**: When SetFit confidence is high (> 0.8), use the canonical profile directly. When lower, blend toward a neutral center (all 0.5) proportionally:

```python
def blend_pase(label: str, confidence: float) -> dict[str, float]:
    canonical = SETFIT_TO_PASE[label]
    neutral = 0.5
    return {k: neutral + (v - neutral) * confidence for k, v in canonical.items()}
```

---

## 5. Recommended Wiring: SetFit → JITAI Interventions

### Wire emotion_context into the screen hot path

Currently `screen.py:58` passes no emotion data to JITAI:
```python
# CURRENT (broken):
intervention = jitai_engine.evaluate(metrics)

# PROPOSED:
intervention = jitai_engine.evaluate(metrics, emotion_context=emotion_context)
```

Since the SenticNet lightweight pipeline runs in a background task (async), the SetFit prediction should run **synchronously** in the hot path — it's fast enough (<50ms):

```python
# In screen.py, after metrics update:
setfit_label, setfit_confidence = setfit_classifier.predict(activity.window_title or activity.app_name)
emotion_context = {
    "setfit_label": setfit_label,
    "setfit_confidence": setfit_confidence,
    "primary_adhd_state": SETFIT_TO_ADHD_STATE[setfit_label],
    "emotional_dysregulation": setfit_label == "overwhelmed" and setfit_confidence > 0.7,
    "frustration_detected": setfit_label == "frustrated" and setfit_confidence > 0.7,
    "anxiety_detected": setfit_label == "anxious" and setfit_confidence > 0.7,
}
intervention = jitai_engine.evaluate(metrics, emotion_context=emotion_context)
```

### New JITAI rules enabled by SetFit

| Rule | Trigger | EF Domain | Intervention Type |
|------|---------|-----------|-------------------|
| **Rule 4a** (existing) | `emotional_dysregulation` (overwhelmed, confidence > 0.7) | `self_regulation_emotion` | Grounding exercise, vent option, break |
| **Rule 4b** (new) | `frustration_detected` AND `context_switch_rate > 8` | `self_regulation_emotion` | Acknowledge frustration, task narrowing, 5-min break |
| **Rule 4c** (new) | `anxiety_detected` AND `distraction_ratio > 0.4` | `self_regulation_emotion` | Breathing exercise, brain dump, task prioritization |
| **Rule 4d** (new) | `disengaged` label persists > 10 min | `self_motivation` | Micro-task suggestion, body doubling, reward nudge |

### Confidence gating

Never trigger an emotion-based intervention when SetFit confidence < 0.6. False positives are worse than missed interventions for ADHD users (unnecessary interruptions destroy flow).

---

## 6. Pipeline Architecture: Where Each System Runs

### Hot Path: Screen Activity (every ~2 seconds)

```
Swift App → POST /screen/activity
  ↓ SYNCHRONOUS (<100ms target)
  ├── 1. Rule-based classifier (<5ms)
  ├── 2. Metrics engine update (<1ms)
  ├── 3. SetFit prediction (<50ms)          ← ADD THIS
  ├── 4. JITAI evaluate(metrics, emotion)   ← WIRE emotion_context
  └── 5. Return response
  ↓ BACKGROUND (async, non-blocking)
  └── SenticNet lightweight (emotion + engagement + intensity, ~500ms)
      └── Store SenticAnalysis DB row
```

### Warm Path: Chat / Vent (user-initiated, latency tolerant)

```
User message → POST /chat/message or /vent/chat/stream
  ↓ SYNCHRONOUS
  ├── 1. SenticNet full pipeline (all 13 APIs, ~2-3s)
  │     └── SetFit overrides primary_emotion at the end
  ├── 2. Safety gate (if critical → crisis response)
  ├── 3. Build senticnet_context dict
  ├── 4. LLM generation with context injection
  └── 5. Return response + persist to Mem0
```

### Cold Path: Dashboard (polling every 30s)

```
Swift App → GET /api/v1/dashboard/stats
  ↓
  ├── Aggregate daily activity from DB
  ├── Read recent SenticAnalysis rows (last 24h)
  ├── NEW: Use SetFit labels from recent predictions for radar
  └── Return dashboard payload
```

---

## 7. Per-Feature Mapping

| Product Feature | SenticNet Role | SetFit Role |
|----------------|---------------|-------------|
| **Emotion Radar** (dashboard) | None (too slow/inaccurate for labels; Hourglass only from full pipeline) | **Primary**: Label → PASE mapping for radar shape |
| **JITAI Interventions** (real-time) | None in hot path (runs in background) | **Primary**: Emotion-aware rules (4a-4d), confidence gating |
| **Chat coaching** (LLM context) | **Primary**: Full-pipeline dimensional scores, concepts, safety, engagement, wellbeing | **Primary**: Overrides emotion label for coaching strategy selection |
| **Vent empathy** (LLM context) | **Primary**: Full-pipeline polarity tracking, escalation detection, safety | **Primary**: Overrides emotion label for tone calibration |
| **Brain dump** (capture) | Lightweight: engagement + intensity | **Primary**: Emotion label stored in Mem0 |
| **Safety detection** (crisis gate) | **Sole source**: Depression + toxicity + intensity | None (SetFit has no safety capability) |
| **XAI explanations** (why/how) | **Primary**: Concept extraction, dimensional scores for Concept Bottleneck | **Supporting**: Emotion label used in explanation text |
| **Vent escalation** (session tracking) | **Primary**: Polarity score tracking across messages | None |
| **Personality** (long-term) | **Sole source**: Big 5 traits from ensemble | None |

---

## 8. Summary: The Complementary Roles

```
┌──────────────────────────────────────────────────────────┐
│                    ADHD Second Brain                      │
│                                                          │
│  ┌─────────────────┐        ┌─────────────────────────┐  │
│  │    SetFit        │        │     SenticNet APIs      │  │
│  │  (on-device)     │        │     (cloud service)     │  │
│  │                  │        │                         │  │
│  │ WHAT emotion     │        │ HOW MUCH (dimensional)  │  │
│  │ • 6 ADHD labels  │        │ • Intensity/arousal     │  │
│  │ • 86% accuracy   │        │ • Engagement level      │  │
│  │ • <50ms latency  │        │ • Wellbeing score       │  │
│  │ • Works offline  │        │ • Polarity (pos/neg)    │  │
│  │                  │        │                         │  │
│  │ DRIVES:          │        │ WHY (context)           │  │
│  │ • Emotion Radar  │        │ • Concept extraction    │  │
│  │ • JITAI rules    │        │ • Aspect analysis       │  │
│  │ • LLM strategy   │        │ • Personality profile   │  │
│  │ • Mem0 tagging   │        │                         │  │
│  │                  │        │ SAFETY (non-negotiable)  │  │
│  │                  │        │ • Depression detection   │  │
│  │                  │        │ • Toxicity detection     │  │
│  │                  │        │ • Crisis gating          │  │
│  │                  │        │                         │  │
│  │                  │        │ DRIVES:                  │  │
│  │                  │        │ • Safety gate            │  │
│  │                  │        │ • LLM dimensional ctx    │  │
│  │                  │        │ • XAI explanations       │  │
│  │                  │        │ • Vent escalation        │  │
│  │                  │        │ • Coaching depth         │  │
│  └─────────────────┘        └─────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            Behavioral Metrics Engine                  │ │
│  │  (in-memory, always-on, <1ms)                        │ │
│  │                                                      │ │
│  │  DRIVES:                                             │ │
│  │  • behavioral_state (focused/distracted/idle/...)    │ │
│  │  • JITAI rules 1-3 (distraction, disengagement,     │ │
│  │    hyperfocus)                                       │ │
│  │  • Focus timeline, context switches, streaks         │ │
│  │  • Dashboard live metrics                            │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**SetFit = fast, accurate emotion labeling (WHAT)**
**SenticNet = rich dimensional analysis + safety (HOW MUCH + WHY + SAFE?)**
**Behavioral Metrics = real-time screen activity patterns (WHAT IS HAPPENING)**

All three systems complement each other. None should be removed. The fix is **wiring them together properly**.

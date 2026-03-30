# SenticNet API → ADHD Mapping Guide

> How each of SenticNet's 13 affective computing APIs maps to ADHD detection and intervention.

---

## Hourglass of Emotions Framework

SenticNet uses the Hourglass of Emotions model with 4 affective dimensions:

```
        PLEASANTNESS
        (joy ↔ sadness)
            │
    ┌───────┼───────┐
    │       │       │
SENSITIVITY ─┼─ ATTENTION
(fear ↔ anger) │  (interest ↔ disgust)
    │       │       │
    └───────┼───────┘
            │
        APTITUDE
        (trust ↔ surprise)
```

---

## API-to-ADHD Mapping

### Tier 1: Safety-Critical (Always First)

| API | ADHD Relevance | Threshold | Action |
|-----|---------------|-----------|--------|
| **Depression** | Detect depressive states that may present as ADHD symptoms (lack of motivation, fatigue) | >70 critical, >50 moderate | Crisis resources if critical; gentle check-in if moderate |
| **Toxicity** | Detect self-directed negativity / self-criticism common in ADHD self-talk | >60 critical (with depression), >50 moderate | Validate feelings; redirect self-criticism |
| **Intensity** | Detect emotional flooding / escalation — ADHD emotional dysregulation | <-80 extreme negative; >80 extreme positive | Grounding exercises; acknowledge intensity |

### Tier 2: Core Emotional Analysis

| API | ADHD Relevance | Application |
|-----|---------------|-------------|
| **Emotion Recognition** | Map Hourglass emotions to ADHD states (e.g., low attention + high sensitivity = overwhelm) | Drives intervention selection and acknowledgment text |
| **Polarity** | Overall positive/negative — tracks emotional trends | Trend analysis for weekly reviews |
| **Subjectivity** | Subjective = emotional support needed; Objective = practical help needed | Routes chat response style |
| **Sarcasm** | ADHD users may use sarcasm to mask frustration — detect and address underlying emotion | >60 = sarcasm detected; look past surface meaning |

### Tier 3: ADHD-Specific Signals

| API | ADHD Relevance | Derived Signal |
|-----|---------------|----------------|
| **Engagement** | Low engagement → disengagement / task avoidance. ADHD interest-based nervous system | `is_disengaged`: engagement < -30 |
| **Wellbeing** | Maps to overall capacity. Low wellbeing + high intensity = overwhelm | `is_overwhelmed`: intensity > 70 AND wellbeing < -20 |
| **Concept Parsing** | Extract semantic concepts for knowledge graph traversal and explanation generation | Feeds XAI Concept Bottleneck Model |
| **Aspect Extraction** | Topic-level sentiment for understanding what specific aspects cause emotional reactions | Identifies specific triggers |

### Tier 4: Deep Analysis (On Demand)

| API | ADHD Relevance | Application |
|-----|---------------|-------------|
| **Personality** | Big 5 trait prediction for long-term personalization | Adjusts intervention style (e.g., high openness → more creative suggestions) |
| **Ensemble** | Meta-fusion combining all models — highest accuracy | Used for complex coaching queries requiring nuanced understanding |

---

## ADHD-Specific Derived Signals

| Signal | Formula | EF Domain Affected |
|--------|---------|-------------------|
| `is_disengaged` | engagement < -30 | Self-motivation |
| `is_overwhelmed` | intensity > 70 AND wellbeing < -20 | Self-regulation of emotion |
| `is_frustrated` | intensity < -50 AND engagement < 0 | Self-regulation of emotion |
| `emotional_dysregulation` | abs(intensity) > 80 | Self-regulation of emotion |

---

## Pipeline Mode Selection

| Context | APIs Used | Reason |
|---------|----------|--------|
| **Chat/Venting** | All 13 (full pipeline) | Rich emotional context needed for empathetic responses |
| **Screen monitoring (current)** | SetFit classifier + Safety + Engagement (hybrid) | SetFit handles emotion; SenticNet handles safety + engagement. <100ms total |
| **Screen monitoring (legacy)** | Emotion + Engagement + Intensity (3 APIs) | Lightweight SenticNet-only, <500ms — superseded by SetFit in Phase 6 |
| **Safety check** | Depression + Toxicity + Intensity (3 APIs) | Fast safety-only gate |
| **Weekly review** | Aggregated results from stored analyses | No live API calls |

---

## SetFit Integration (Phase 6)

### Before Phase 6
SenticNet's Emotion Recognition API provided the `primary_emotion` field via Hourglass of Emotions mapping. This achieved ~32% accuracy on ADHD-specific emotion states because the Hourglass model was designed for general-purpose emotion recognition, not ADHD behavioral classification.

### After Phase 6
A **SetFit contrastive fine-tuned classifier** (all-mpnet-base-v2 → LogisticRegression, **86% accuracy**) now handles primary emotion classification on the screen monitoring hot path.

### 6 ADHD-Specific Emotion Labels

| Label | Description | ADHD Relevance |
|-------|------------|----------------|
| `joyful` | Positive engagement, satisfaction | Productive flow state |
| `focused` | Deep concentration, task absorption | Healthy focus or potential hyperfocus |
| `frustrated` | Blocked, stuck, irritated | Frustration spiral, EF overload |
| `anxious` | Worried, uncertain, overwhelmed by possibilities | Anxiety comorbidity, RSD |
| `disengaged` | Bored, checked out, avoidant | Task avoidance, dopamine-seeking |
| `overwhelmed` | Emotional flooding, too much input | Emotional dysregulation |

### PASE Radar Profile Mapping

Each SetFit label maps to a canonical PASE (Pleasantness, Attention, Sensitivity, Aptitude) radar profile:

| SetFit Label | ADHD State | P | A | S | Ap |
|-------------|------------|---|---|---|-----|
| joyful | productive_flow | 0.85 | 0.70 | 0.30 | 0.75 |
| focused | productive_flow | 0.60 | 0.90 | 0.20 | 0.80 |
| frustrated | frustration_spiral | 0.15 | 0.40 | 0.80 | 0.30 |
| anxious | anxiety_comorbid | 0.20 | 0.55 | 0.90 | 0.25 |
| disengaged | boredom_disengagement | 0.35 | 0.15 | 0.25 | 0.20 |
| overwhelmed | emotional_dysregulation | 0.10 | 0.30 | 0.85 | 0.15 |

These PASE scores are blended with SetFit confidence and averaged across recent predictions to produce the emotion radar displayed in the dashboard and Notch Island.

### What SenticNet Still Handles

| Signal | Source | Pipeline |
|--------|--------|----------|
| **Safety** (depression, toxicity, intensity) | SenticNet Tier 1 | Both chat and screen |
| **Hourglass dimensions** (pleasantness, attention, sensitivity, aptitude) | SenticNet Tier 2 | Chat only |
| **Polarity, subjectivity, sarcasm** | SenticNet Tier 2 | Chat only |
| **Engagement, wellbeing** | SenticNet Tier 3 | Both (lightweight on screen) |
| **Concepts, aspects** | SenticNet Tier 3 | Chat only |
| **Personality, ensemble** | SenticNet Tier 4 | Chat only (on demand) |
| **Primary emotion classification** | **SetFit** (not SenticNet) | Screen hot path |

### Pipeline Split Summary

| Pipeline | Emotion Source | SenticNet Usage | Latency |
|----------|---------------|-----------------|---------|
| **Screen monitoring** | SetFit (86%, <50ms) | Safety + engagement only (background, async) | <100ms |
| **Chat/Venting** | SenticNet full pipeline (all 13 APIs) | Full Hourglass + safety + engagement + personality | ~3.7s |
| **Vent modal** | SenticNet (4-layer safety) | Crisis detection + semantic analysis | ~2s |
| **Brain dump** | SetFit (emotion tagging) | None (fast capture priority) | <50ms |

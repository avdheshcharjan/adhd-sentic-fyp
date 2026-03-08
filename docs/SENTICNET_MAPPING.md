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
| **Screen monitoring** | Emotion + Engagement + Intensity (3 APIs) | Lightweight, <500ms, window title analysis |
| **Safety check** | Depression + Toxicity + Intensity (3 APIs) | Fast safety-only gate |
| **Weekly review** | Aggregated results from stored analyses | No live API calls |

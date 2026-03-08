# Phase 3: SenticNet Pipeline

> **Timeline**: Week 2–3  
> **Dependencies**: Phase 1 (backend running)  
> **External**: SenticNet API keys (IP-locked, ~1 month expiry)

---

## Overview

SenticNet provides 13 affective computing REST APIs that form the emotional intelligence backbone of the system. This phase implements the HTTP client, 4-tier pipeline orchestrator, and safety-first processing architecture.

---

## The 13 SenticNet APIs

| # | API | Key Config | ADHD Application |
|---|-----|-----------|-----------------|
| 1 | **Concept Parsing** | `SENTIC_CONCEPT_PARSING` | Extract semantic concepts from text |
| 2 | **Subjectivity Detection** | `SENTIC_SUBJECTIVITY` | Route emotional vs practical support |
| 3 | **Polarity Classification** | `SENTIC_POLARITY` | Positive/negative sentiment |
| 4 | **Intensity Ranking** | `SENTIC_INTENSITY` | Escalation detection |
| 5 | **Emotion Recognition** | `SENTIC_EMOTION` | Hourglass of Emotions (4 dimensions) |
| 6 | **Aspect Extraction** | `SENTIC_ASPECT` | Topic-level sentiment breakdown |
| 7 | **Personality Prediction** | `SENTIC_PERSONALITY` | Big 5 traits for personalization |
| 8 | **Sarcasm Identification** | `SENTIC_SARCASM` | Detect sarcasm to avoid misinterpretation |
| 9 | **Depression Categorization** | `SENTIC_DEPRESSION` | 🔴 Safety-critical flag |
| 10 | **Toxicity Spotting** | `SENTIC_TOXICITY` | 🔴 Safety-critical flag |
| 11 | **Engagement Measurement** | `SENTIC_ENGAGEMENT` | User engagement level |
| 12 | **Well-being Assessment** | `SENTIC_WELLBEING` | Overall emotional well-being |
| 13 | **Ensemble (Meta-fusion)** | `SENTIC_ENSEMBLE` | Combined multi-model output |

---

## Key Files to Create

| File | Purpose |
|------|---------|
| `backend/services/senticnet_client.py` | HTTP client for all 13 APIs |
| `backend/services/senticnet_pipeline.py` | 4-tier orchestrator |
| `backend/models/senticnet_result.py` | Pydantic models for results |
| `scripts/test_senticnet_keys.py` | API key validation script |

---

## 4-Tier Pipeline Architecture

```
                    ┌─────────────────────────────────┐
                    │        INPUT TEXT                │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
  TIER 1 (Safety)   │  Depression + Toxicity + Intensity │
  Runs FIRST        │  ↳ If CRITICAL → Emergency exit   │
                    └───────────────┬─────────────────┘
                                    │ (pass if safe)
                    ┌───────────────▼─────────────────┐
  TIER 2 (Emotion)  │  Emotion + Polarity + Subjectivity │
                    │  + Sarcasm                         │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
  TIER 3 (ADHD)     │  Engagement + Wellbeing + Concepts │
                    │  + Aspects                         │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
  TIER 4 (Deep)     │  Personality + Ensemble            │
                    │  (only if needed)                  │
                    └─────────────────────────────────┘
```

---

## Pipeline Modes

| Mode | APIs Called | Latency | Use Case |
|------|-----------|---------|----------|
| **Full Analysis** | All 13 (4 tiers) | ~2–3s | Chat/venting messages |
| **Lightweight** | Emotion + Engagement + Intensity (3 APIs) | <500ms | Window title analysis during screen monitoring |
| **Safety Check** | Depression + Toxicity + Intensity (3 APIs) | <500ms | Quick safety-only check |

---

## SenticNet HTTP Client

### API Format
```
GET https://sentic.net/api/{LANG}/{KEY}.py?text={TEXT}
```

### Constraints
- **Text limit**: Max ~1000 words (8000 chars server limit)
- **Illegal characters**: `& # ; { }` → replace with `:` or remove
- **Keys**: Case-sensitive, IP-locked
- **Auth**: API key in URL path (not header)
- **Response**: JSON

### Concurrent Calls
APIs within the same tier are called **concurrently** using `asyncio.gather()`. This keeps latency bounded by the slowest API in each tier, not the sum.

---

## Safety Thresholds

> ⚠️ **Safety is non-negotiable.** The safety check runs FIRST in every pipeline. If critical, skip all other processing and show crisis resources immediately.

| Level | Condition | Action |
|-------|-----------|--------|
| **CRITICAL** | Depression > 70 AND Toxicity > 60 | Emergency response + crisis resources (988 Lifeline) |
| **HIGH** | Depression > 70 OR Intensity < -80 | Gentle check-in, suggest professional support |
| **MODERATE** | Toxicity > 50 (self-directed) | Validate feelings, offer grounding exercises |
| **NORMAL** | Below all thresholds | Standard processing |

---

## Output Models

### `EmotionProfile`
```python
class EmotionProfile(BaseModel):
    primary_emotion: str           # e.g., "anger", "sadness", "joy"
    hourglass_dimensions: dict     # {pleasantness, attention, sensitivity, aptitude}
    polarity: str                  # "positive", "negative", "neutral"
    polarity_score: float          # -100 to 100
    is_subjective: bool            # Subjective vs objective text
    sarcasm_score: float           # 0–100
    sarcasm_detected: bool         # True if sarcasm_score > 60
```

### `SafetyFlags`
```python
class SafetyFlags(BaseModel):
    level: str                     # "critical", "high", "moderate", "normal"
    depression_score: float
    toxicity_score: float
    intensity_score: float
    is_critical: bool
```

### `ADHDRelevantSignals`
```python
class ADHDRelevantSignals(BaseModel):
    engagement_score: float        # -100 to 100
    wellbeing_score: float         # -100 to 100
    intensity_score: float         # -100 to 100
    is_disengaged: bool            # engagement < -30
    is_overwhelmed: bool           # intensity > 70 AND wellbeing < -20
    is_frustrated: bool            # intensity < -50 AND engagement < 0
    emotional_dysregulation: bool  # abs(intensity) > 80
```

---

## Important Notes

1. **API keys expire after ~1 month** and are IP-locked. Test early and request new ones if needed.

2. **Response format varies per endpoint.** The `_extract_score()` method must be adapted based on actual API responses. Test each endpoint individually first and log raw responses.

3. **Retry and error handling**: Use `httpx` with 30s timeout. Individual API failures should not crash the pipeline — use `return_exceptions=True` in `asyncio.gather()`.

4. **Rate limiting**: No documented rate limits, but be cautious with concurrent calls. The pipeline dispatches up to 4 concurrent requests per tier.

---

## Verification Checklist

- [ ] `test_senticnet_keys.py` validates all 13 API keys successfully
- [ ] Each API returns valid JSON for sample text
- [ ] Safety check correctly identifies CRITICAL scenarios
- [ ] Full pipeline completes in < 3 seconds
- [ ] Lightweight pipeline completes in < 500ms
- [ ] Failed APIs don't crash the pipeline
- [ ] Illegal characters are sanitized before API calls
- [ ] `POST /chat/message` returns full SenticNet analysis

### Test Command
```bash
curl -X POST http://localhost:8420/chat/message \
  -H "Content-Type: application/json" \
  -d '{"text": "I am so frustrated I cant focus on anything today"}'
```

---

## Next Phase

→ [Phase 4: XAI & JITAI Engine](PHASE_4_XAI_JITAI_ENGINE.md) (consumes SenticNet output)

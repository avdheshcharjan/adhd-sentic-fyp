# Testing Strategy

> Unit tests, integration tests, and key test scenarios for the ADHD Second Brain system.

---

## Test Structure

```
backend/tests/
├── test_senticnet_client.py      # Mock HTTP, sanitization, error handling
├── test_senticnet_pipeline.py    # Tier routing, safety thresholds
├── test_activity_classifier.py   # All 4 layers with known apps/URLs
├── test_adhd_metrics.py          # Metric computation, state transitions
├── test_jitai_engine.py          # Intervention rules, cooldowns, adaptive behavior
├── test_xai_explainer.py         # Explanation generation
├── test_whoop_service.py         # Mock Whoop API, morning briefing logic
└── test_chat_processor.py        # Full chat pipeline
```

---

## Unit Tests (pytest)

### Activity Classifier
- Known apps return correct categories (VSCode → development, Spotify → entertainment)
- Known URLs return correct categories (github.com → development)
- Window title keywords match (contains "youtube" → entertainment)
- Unknown apps/URLs return "other"
- URL parent domain fallback (mail.google.com → google.com)

### ADHD Metrics Engine
- Context switch rate calculated correctly over 5-minute window
- Focus score reflects productive time ratio
- Distraction ratio reflects distracting time ratio
- Hyperfocus detected after 3+ hours
- Behavioral states transition correctly (idle → focused → distracted)
- Deque maxlen limits memory usage

### JITAI Engine

```python
def test_distraction_spiral_triggers_intervention():
    """12+ switches in 5 min + >50% distraction ratio = intervention"""
    metrics = ADHDMetrics(context_switch_rate_5min=15, distraction_ratio=0.65)
    intervention = engine.evaluate(metrics)
    assert intervention is not None
    assert intervention.type == "distraction_spiral"
    assert len(intervention.actions) <= 3

def test_focused_state_blocks_intervention():
    """Never interrupt someone who is focused"""
    metrics = ADHDMetrics(behavioral_state="focused")
    assert engine.evaluate(metrics) is None

def test_cooldown_prevents_spam():
    """No intervention within cooldown period"""
    engine.record_response("test", "breathe", dismissed=False)
    metrics = ADHDMetrics(context_switch_rate_5min=20, distraction_ratio=0.8)
    assert engine.evaluate(metrics) is None

def test_adaptive_cooldown_on_dismissals():
    """Cooldown increases after repeated dismissals"""
    for _ in range(3):
        engine.record_response("test", None, dismissed=True)
    assert engine.cooldown_seconds > 300
```

### SenticNet Client
- Text sanitization removes illegal chars (`& # ; { }`)
- Text truncated at 8000 chars
- API URL constructed correctly
- Concurrent calls return results mapped to API names
- Failed APIs don't crash `call_multiple`

### SenticNet Pipeline
- Safety check runs before other tiers
- CRITICAL safety flag triggers emergency result
- Full analysis returns all 4 tiers
- Lightweight analysis calls only 3 APIs
- Score extraction handles varying response formats

### XAI Explainer
- WHAT explanations include metric values
- WHY explanations reference SenticNet emotions
- HOW explanations provide counterfactual suggestions
- All intervention types have templates

---

## Integration Tests

| Test | Components | Notes |
|------|-----------|-------|
| Swift → Backend round-trip | Swift app + `POST /screen/activity` | Sample data, validate response shape |
| SenticNet API calls | `senticnet_client.py` + real keys | Mark `@slow`, skip in CI |
| Whoop OAuth flow | `api/whoop.py` + Whoop cloud | End-to-end with real credentials |
| OpenClaw → Backend → Response | OpenClaw skill + `POST /chat/message` | Full venting pipeline |
| Dashboard data fetch | React + `GET /insights/dashboard` | Validate all chart data present |

---

## Test Commands

```bash
# Run all unit tests
cd backend && python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_jitai_engine.py -v

# Run with coverage
python -m pytest tests/ --cov=services --cov-report=html

# Run only fast tests (skip @slow SenticNet API tests)
python -m pytest tests/ -v -m "not slow"
```

---

## FYP Evaluation Data

Every decision point should be logged for the FYP report:

1. **Activity classifications** — input + output + which layer matched
2. **JITAI decisions** — metrics snapshot + intervention type + user response
3. **SenticNet analyses** — raw results + derived signals
4. **Intervention effectiveness** — accepted/dismissed + optional rating
5. **Timestamps** on everything for temporal analysis

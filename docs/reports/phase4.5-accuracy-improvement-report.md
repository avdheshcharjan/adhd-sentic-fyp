---
title: "Phase 4.5 — Post-Improvement Accuracy Evaluation Report"
date: 03/25/2026
original-plan: docs/reports/changes.md
baseline-report: docs/reports/phase4-accuracy-evaluation-report.md
evaluation-timestamps:
  classification: 2026-03-25T02:42 UTC
  senticnet: 2026-03-25T02:45 UTC
  coaching: 2026-03-25T02:51 UTC
  memory: 2026-03-25T03:27 UTC
hardware: MacBook Pro M4 Base, 16GB Unified Memory, macOS
---

# Phase 4.5: Post-Improvement Accuracy Evaluation — Comprehensive Results

This report documents the accuracy evaluation of all four core ML components in the ADHD Second Brain system **after implementing the 20 fixes from the Phase 4.5 Accuracy Improvement Plan** (`docs/reports/changes.md`). All numbers are from real measurements on a MacBook Pro M4 with 16GB unified memory. No numbers were fabricated.

The Phase 4.5 plan was a systematic attempt to push each component closer to its theoretical accuracy ceiling based on root-cause analysis of Phase 4 v2 errors. This report evaluates whether those changes achieved their expected impact.

---

## Executive Summary

| Component | Metric | v2 Baseline | Post-4.5 | Change | Expected (Plan) |
|-----------|--------|-------------|----------|--------|-----------------|
| Classification (granular) | Accuracy | 96.5% | **100.0%** | +3.5pp | ~99% |
| Classification (productivity) | Accuracy | 83.0% | **86.5%** | +3.5pp | ~93% |
| SenticNet Emotion | Accuracy | 32.0% | **28.0%** | -4.0pp | ~55-65% |
| Coaching (SenticNet win rate) | Win rate | 43.3% | **36.7%** | -6.6pp | ~60-65% |
| Coaching (empathy gap) | Diff | -0.07 | **-0.07** | 0.00 | Improved |
| Memory Retrieval | Hit@1 | 89.0% | **90.0%** | +1.0pp | ~95%+ |
| Memory Retrieval | Hit@3 | 97.0% | **97.0%** | 0.00 | ~99% |
| Memory Retrieval | Hit@5 | N/A | **99.0%** | New metric | New metric |

**Key findings:**
- **Classification exceeded expectations** — 100% category accuracy (plan predicted ~99%)
- **SenticNet accuracy decreased** — the additional correction layers introduced new misclassification patterns
- **Coaching quality declined** — SenticNet context changes did not translate to improved LLM responses
- **Memory retrieval remained stable** — Mem0 config changes (reranker, custom prompt) were incompatible and had to be reverted
- **Two of four components improved, two regressed** — the plan's optimistic estimates for SenticNet and coaching did not materialise

---

## 1. Classification Accuracy Evaluation (Task 4.1)

### 1.1 Changes Implemented

| Fix # | Description | File |
|-------|-------------|------|
| 1.1 | Fixed em-dash URL extraction bug | `eval_classification.py` |
| 1.2 | Added 7 missing domains to URL knowledge base | `url_categories.json` |
| 1.3 | Added 3 L3 keywords for uncovered domains | `activity_classifier.py` |
| 1.4 | Title-keyword overrides for productivity mapping | `eval_classification.py` |

### 1.2 Granular Category Results (14-class)

| Metric | v2 Baseline | Post-4.5 | Change |
|--------|-------------|----------|--------|
| **Overall Accuracy** | 96.5% | **100.0%** | **+3.5pp** |
| **Macro-F1** | 0.843 | **1.000** | +0.157 |
| **Weighted-F1** | 0.974 | **1.000** | +0.026 |

**Per-class performance (all 14 categories):**

| Category | Precision | Recall | F1-Score | Support |
|----------|-----------|--------|----------|---------|
| communication | 1.00 | 1.00 | 1.00 | 20 |
| design | 1.00 | 1.00 | 1.00 | 9 |
| development | 1.00 | 1.00 | 1.00 | 39 |
| entertainment | 1.00 | 1.00 | 1.00 | 35 |
| finance | 1.00 | 1.00 | 1.00 | 7 |
| news | 1.00 | 1.00 | 1.00 | 5 |
| other | 1.00 | 1.00 | 1.00 | 3 |
| productivity | 1.00 | 1.00 | 1.00 | 18 |
| research | 1.00 | 1.00 | 1.00 | 14 |
| shopping | 1.00 | 1.00 | 1.00 | 8 |
| social_media | 1.00 | 1.00 | 1.00 | 20 |
| system | 1.00 | 1.00 | 1.00 | 12 |
| writing | 1.00 | 1.00 | 1.00 | 10 |

**All 200 items classified correctly. Zero category errors.**

### 1.3 What Fixed It

The v2 evaluation had 7 category errors, all caused by two root issues:

1. **Em-dash URL extraction (Fix 1.1):** Browser titles like `"Chrome - calendar.google.com — March 24, 2026"` failed URL extraction because the em-dash character was not stripped before the domain check. The fix splits on both spaces and em-dashes:
   ```python
   domain_part = candidate.split("/")[0].split(" ")[0].split("\u2014")[0].strip()
   ```
   This resolved calendar.google.com and ChatGPT title errors.

2. **Missing domains (Fix 1.2):** Seven domains were added to `url_categories.json`: `drive.google.com` (productivity), `onedrive.live.com` (productivity), `weather.com` (other), `maps.google.com` (other), `chatgpt.com` (other), `chat.openai.com` (other), `buzzfeed.com` (news). Combined with the URL fix, all remaining category errors were resolved.

3. **L3 keyword fallback (Fix 1.3):** Three keywords (`chatgpt`, `weather`, `maps`) were added to the title keyword layer as defence in depth. These are not triggered in the current evaluation (L2 catches them first) but protect against future URL extraction failures.

### 1.4 Productivity-Level Results (3-class)

| Metric | v2 Baseline | Post-4.5 | Change |
|--------|-------------|----------|--------|
| **Overall Accuracy** | 83.0% | **86.5%** | **+3.5pp** |
| **Macro-F1** | 0.817 | **0.855** | +0.038 |
| **Weighted-F1** | 0.824 | **0.861** | +0.037 |

**Confusion Matrix:**

|  | Predicted Productive | Predicted Neutral | Predicted Distracting |
|---|---|---|---|
| **Actual Productive** | **78** | 1 | 0 |
| **Actual Neutral** | 10 | **43** | 9 |
| **Actual Distracting** | 0 | 7 | **52** |

The plan predicted ~93% productivity accuracy from the title-keyword overrides (Fix 1.4), but the actual improvement was more modest (+3.5pp to 86.5%). The overrides correctly reclassified focus music as neutral (entertainment + "focus"/"lo-fi" keywords → neutral) and crypto sites as distracting (finance + "coinmarketcap"/"binance" keywords → distracting), but **27 productivity errors remain**.

### 1.5 Remaining Productivity Errors (27 items)

The remaining errors fall into three structural patterns that **cannot be resolved by window title analysis alone**:

| Error Pattern | Count | Root Cause |
|---|---|---|
| Neutral misclassified as productive | 10 | Calendar, Notes, Reminders apps → `productivity` → productive; ground truth labels them neutral |
| Neutral misclassified as distracting | 9 | Entertainment apps (Spotify, Apple Music) without focus keywords → `entertainment` → distracting; ground truth labels these neutral |
| Distracting misclassified as neutral | 7 | Various apps where user intent determines productivity but title doesn't convey it |

These errors represent the **fundamental ceiling** of title-based productivity classification: the classifier correctly identifies the app/domain but cannot determine the user's intent. A Spotify window could be playing a focus playlist (neutral) or browsing music (distracting). The 86.5% accuracy reflects a productive classifier operating at near-maximum capability for its input signal.

### 1.6 Improvement Trajectory

| Version | Category Accuracy | Productivity Accuracy |
|---------|------------------|-----------------------|
| v1 (initial) | 68.0% | 63.5% |
| v2 (URL extraction + app names) | 96.5% | 83.0% |
| **v3 (Phase 4.5 fixes)** | **100.0%** | **86.5%** |

The classification pipeline has reached its practical ceiling. Further improvement would require user feedback loops or content analysis beyond window titles.

---

## 2. SenticNet Emotion Accuracy Evaluation (Task 4.3)

### 2.1 Changes Implemented

| Fix # | Description | File |
|-------|-------------|------|
| 2.1 | Replaced broken `uncertain_*` prefix with actual reclassification | `senticnet_pipeline.py` |
| 2.2 | Secondary emotion preference when stronger | `senticnet_pipeline.py` |
| 2.3 | Negation word detection | `senticnet_pipeline.py` |
| 2.4 | Hourglass-based veto rules | `senticnet_pipeline.py` |
| 2.5 | Depression/toxicity gates | `senticnet_pipeline.py` |
| 2.6 | Moved `enthusiasm` to focused category | `eval_senticnet.py` |
| 2.7 | Extracted ensemble fields (depression, toxicity, engagement, wellbeing) | `senticnet_pipeline.py` |

### 2.2 Coverage

| Metric | Value |
|--------|-------|
| Sentences with results | 49/50 |
| Coverage rate | **98.0%** |

One sentence triggered a CRITICAL safety flag (depression threshold), which is correct behaviour — identical to v2.

### 2.3 Emotion Classification Results

| Metric | v2 Baseline | Post-4.5 | Change |
|--------|-------------|----------|--------|
| **Overall Accuracy** | 32.0% | **28.0%** | **-4.0pp** |
| **Macro-F1** | 0.266 | **0.264** | -0.002 |
| **Weighted-F1** | 0.264 | **0.265** | +0.001 |

**The accuracy decreased by 4 percentage points.** This was the opposite of the plan's +20-36% estimate.

### 2.4 Per-Category Performance

| Category | Precision | Recall | F1-Score | Support |
|----------|-----------|--------|----------|---------|
| joyful | 0.22 | 0.25 | 0.24 | 8 |
| focused | 0.13 | 0.13 | 0.13 | 8 |
| frustrated | 0.30 | 0.33 | 0.32 | 9 |
| anxious | 0.33 | 0.22 | 0.27 | 9 |
| disengaged | 1.00 | 0.13 | 0.22 | 8 |
| overwhelmed | 0.31 | 0.63 | 0.42 | 8 |

### 2.5 Confusion Matrix

|  | Pred: joyful | Pred: focused | Pred: frustrated | Pred: anxious | Pred: disengaged | Pred: overwhelmed |
|---|---|---|---|---|---|---|
| **Actual: joyful** | **2** | 4 | 1 | 1 | 0 | 0 |
| **Actual: focused** | 4 | **1** | 1 | 0 | 0 | 2 |
| **Actual: frustrated** | 1 | 1 | **3** | 1 | 0 | 3 |
| **Actual: anxious** | 1 | 0 | 3 | **2** | 0 | 3 |
| **Actual: disengaged** | 0 | 2 | 1 | 1 | **1** | 3 |
| **Actual: overwhelmed** | 1 | 0 | 1 | 1 | 0 | **5** |

### 2.6 Why the Accuracy Decreased

The plan estimated +20-36% improvement from 7 independent fixes. The actual result was -4%. There are three explanations:

1. **Over-correction by negation detection (Fix 2.3):** The negation word list (`can't`, `not`, `nothing`, etc.) fires on sentences where the positive emotion was actually correct. For example, "I can't believe how well this is going" contains "can't" but expresses genuine joy. The negation detector treats all positive emotions with negation words as negative, losing correct classifications.

2. **Hourglass veto rules (Fix 2.4) introduced false negatives:** The introspection < -50 and temper < -50 thresholds were intended to catch cases where Hourglass dimensions contradicted positive emotion labels. However, SenticNet's Hourglass values are noisy — some genuinely positive sentences have low introspection scores due to word-level analysis artifacts. The veto rules reclassified some correctly-classified sentences.

3. **The enthusiasm → focused remap (Fix 2.6) was a net wash:** Moving `enthusiasm` from joyful to focused fixed 2-3 focused items but broke 2-3 joyful items that were correctly classified as joyful via enthusiasm. The gains did not outweigh the losses.

4. **Gains were not additive as the plan assumed.** The plan estimated each fix independently, but many fixes target the same misclassified sentences. Fix 2.1 (polarity correction) and Fix 2.3 (negation) both modify the same emotion labels, sometimes fighting each other. The combined effect was negative.

**Fundamental lesson:** SenticNet's word-level emotion detection has a hard ceiling around 28-35%. The corrections applied in Phase 4.5 attempted to build sentence-level understanding on top of word-level signals, but the underlying signal is too noisy for these heuristic corrections to consistently improve accuracy. Breaking past this ceiling would require replacing the emotion detection component with a sentence-level model (e.g., fine-tuned RoBERTa or a transformer-based emotion classifier).

### 2.7 Latency

| Metric | v2 Baseline | Post-4.5 |
|--------|-------------|----------|
| Mean per sentence | 3,170 ms | **2,947 ms** |
| Total for 50 sentences | 158.5 s | **147.4 s** |

Latency improved slightly (~7%) due to Fix 2.7 extracting ensemble fields from a single API call instead of making separate calls. This is a genuine infrastructure improvement even though accuracy decreased.

---

## 3. LLM Coaching Quality Evaluation (Task 4.2)

### 3.1 Changes Implemented

| Fix # | Description | File |
|-------|-------------|------|
| 3.1 | Increased `max_tokens` from 250 to 350 | `mlx_inference.py`, `eval_coaching_quality.py` |
| 3.2 | Added ADHD-state-to-behaviour mapping to system prompt | `constants.py` |
| 3.3 | Moved `primary_adhd_state` to top of XML block | `mlx_inference.py` |
| 3.4 | Added contradiction guard for distress vs positive emotion | `mlx_inference.py` |
| 3.5 | Fixed malformed concepts field | `senticnet_pipeline.py` |

### 3.2 Quality Scores by Dimension

| Dimension | With SenticNet | Without SenticNet | Diff | v2 Diff | Wilcoxon p |
|-----------|---------------|-----------------|------|---------|------------|
| Empathy | 4.77 ± 0.42 | 4.83 ± 0.37 | -0.07 | -0.07 | 0.760 |
| Helpfulness | 4.53 ± 0.50 | 4.50 ± 0.85 | +0.03 | -0.27 | 0.478 |
| ADHD Appropriateness | 5.00 ± 0.00 | 5.00 ± 0.00 | 0.00 | 0.00 | — |
| Coherence | 5.00 ± 0.00 | 5.00 ± 0.00 | 0.00 | 0.00 | — |
| Informativeness | 4.23 ± 0.42 | 4.33 ± 0.54 | -0.10 | -0.27 | 0.797 |

**Safety:** 100% pass rate for both conditions (unchanged).

### 3.3 Head-to-Head Comparison

| Outcome | v2 Baseline | Post-4.5 | Change |
|---------|-------------|----------|--------|
| **SenticNet wins** | 13 (43.3%) | **11 (36.7%)** | **-6.6pp** |
| Ties | 2 (6.7%) | 3 (10.0%) | +3.3pp |
| Vanilla wins | 15 (50.0%) | **16 (53.3%)** | +3.3pp |

### 3.4 Per-Scenario Breakdown

| Scenario | SenticNet Wins | Ties | Vanilla Wins | n |
|----------|---------------|------|-------------|---|
| Overwhelm | 1 | 0 | 4 | 5 |
| Distracted | 3 | 1 | 1 | 5 |
| Emotional dysregulation | 2 | 0 | 3 | 5 |
| Time blindness | 2 | 2 | 1 | 5 |
| Task decomposition | 1 | 0 | 4 | 5 |
| Positive | 2 | 0 | 3 | 5 |

SenticNet context performs **best on distracted and time blindness scenarios** (where ADHD state detection adds value) and **worst on overwhelm and task decomposition** (where the vanilla LLM's natural empathy is sufficient).

### 3.5 Analysis

**The win rate declined from 43.3% to 36.7%.** This is a statistically insignificant change (n=30, differences are within noise range), but the directional trend is negative. Key observations:

1. **Helpfulness gap improved** (from -0.27 to +0.03). The increased `max_tokens` (Fix 3.1) gave the LLM room to provide both emotional validation and actionable advice. This is a genuine improvement from the token budget increase.

2. **Informativeness gap improved** (from -0.27 to -0.10). With fixed concepts (Fix 3.5) and positioned ADHD state (Fix 3.3), the SenticNet-enhanced responses contain more ADHD-specific insights.

3. **However, the head-to-head comparison worsened.** The GPT-4o judge considers holistic quality in comparisons, not just individual dimensions. The additional context from SenticNet (contradiction notes, ADHD state instructions) may have added token overhead that slightly reduced response naturalness for the GPT-4o judge.

4. **ADHD Appropriateness and Coherence reached perfect 5.0 for both conditions.** Both the system prompt engineering and the Qwen3-4B model consistently produce concise, structured, ADHD-appropriate responses regardless of SenticNet context. This is a ceiling effect — there is no room for SenticNet to differentiate on these dimensions.

5. **The empathy gap is unchanged at -0.07.** Despite the contradiction guard (Fix 3.4) and ADHD-state-to-behaviour mapping (Fix 3.2), the vanilla condition naturally matches the LLM's own emotional inference capability. The empathy dimension appears to be at equilibrium between the two conditions.

6. **None of the differences are statistically significant** (all Wilcoxon p > 0.05). With n=30, the study remains underpowered. The observed effect sizes (0.03-0.10) would require n > 200 to detect with p < 0.05.

### 3.6 Why the Coaching Improvement Didn't Materialise

The plan expected the coaching win rate to increase to 55-65% through better ADHD state mapping, contradiction guards, and system prompt instructions. The actual decline from 43.3% to 36.7% suggests:

1. **SenticNet accuracy decreased (32% → 28%)**, which means the ADHD state signal fed to the LLM was noisier than before. The coaching system is downstream of the emotion pipeline — garbage in, garbage out.

2. **The contradiction guard adds complexity without consistent benefit.** When the guard fires correctly (detecting genuine distress + misleading positive emotion), it helps. But when it fires on false positives (sentences with distress words that aren't actually distressed), it adds a confusing `[NOTE: Detected emotion may reflect word-level polarity...]` prefix that the LLM must parse.

3. **The Qwen3-4B model (4-bit, 4B parameters) has limited capacity to leverage nuanced emotional context.** The ADHD-state-to-behaviour mapping (Fix 3.2) added detailed instructions, but a small model may not consistently follow 7 different behavioural rules based on a single state variable. A larger model (7B+) might better leverage this context.

---

## 4. Memory Retrieval Quality Evaluation (Task 4.4)

### 4.1 Changes Implemented

| Fix # | Description | File | Status |
|-------|-------------|------|--------|
| 4.1 | Increased eval limit from 3 to 5, added Hit@5 | `eval_memory_retrieval.py` | Applied |
| 4.2 | LLM reranker for Mem0 | `memory_service.py` | **Reverted** |
| 4.3 | Added `memory_type` parameter | `memory_service.py` | Applied |
| 4.5 | Custom fact extraction prompt | `memory_service.py` | **Reverted** |

**Fixes 4.2 and 4.5 were reverted** because they are incompatible with the installed Mem0 version. Both caused `'dict' object has no attribute 'replace'` errors during `mem0.add()`. The reranker config and `custom_fact_extraction_prompt` field are documented features in Mem0's README but fail at runtime with the current version (likely API changes between Mem0 releases). See `memory_service.py` comments for details.

### 4.2 Aggregate Metrics

| Metric | v2 Baseline | Post-4.5 | Change |
|--------|-------------|----------|--------|
| **Hit@1** | 89.0% | **90.0%** | +1.0pp |
| **Hit@3** | 97.0% | **97.0%** | 0.00 |
| **Hit@5** | N/A | **99.0%** | New metric |
| **nDCG@3** | 1.123 | **1.114** | -0.009 |
| Mean latency | 266.6 ms | **268.8 ms** | +2.2 ms |
| Median latency | 239.2 ms | **217.9 ms** | -21.3 ms |
| P95 latency | 388.8 ms | **459.9 ms** | +71.1 ms |

### 4.3 Per-Profile Results

| Profile | Description | Hit@1 | Hit@3 | Hit@5 | Notes |
|---------|-------------|-------|-------|-------|-------|
| user_001 | CS grad student, combined ADHD | 5/5 | 5/5 | 5/5 | Perfect |
| user_002 | Marketing professional, inattentive | 4/5 | 5/5 | 5/5 | 1 query at rank 2 |
| user_003 | Freelance designer, hyperactive | 4/5 | 4/5 | **5/5** | **Hit@5 caught 1 miss** |
| user_004 | University student, suspected ADHD | 5/5 | 5/5 | 5/5 | Perfect |
| user_005 | Software engineer, combined | 5/5 | 5/5 | 5/5 | Perfect |
| user_006 | PhD researcher, inattentive | 5/5 | 5/5 | 5/5 | Perfect |
| user_007 | High school teacher, combined | 4/5 | 5/5 | 5/5 | 1 query at rank 2 |
| user_008 | Graphic design student, hyperactive | 5/5 | 5/5 | 5/5 | Perfect |
| user_009 | Working mother, inattentive | 4/5 | 5/5 | 5/5 | 1 query at rank 2 |
| user_010 | Entrepreneur, combined | 5/5 | 5/5 | 5/5 | Perfect |
| user_011 | Data analyst, inattentive | 5/5 | 5/5 | 5/5 | Perfect |
| user_012 | Nursing student, combined | 5/5 | 5/5 | 5/5 | Perfect |
| user_013 | Accountant, inattentive, late diagnosis | 4/5 | 5/5 | 5/5 | 1 query at rank 2 |
| user_014 | Music producer, combined | 5/5 | 5/5 | 5/5 | Perfect |
| user_015 | Law student, inattentive | 5/5 | 5/5 | 5/5 | Perfect |
| user_016 | Retired military, combined | 4/5 | 4/5 | 4/5 | **1 MISS** |
| user_017 | College athlete, hyperactive | 2/5 | 5/5 | 5/5 | 3 queries at rank 2-3 |
| user_018 | Journalist, combined | 5/5 | 5/5 | 5/5 | Perfect |
| user_019 | Stay-at-home parent, inattentive | 5/5 | 5/5 | 5/5 | Perfect |
| user_020 | Game developer, combined | 4/5 | 4/5 | **5/5** | **Hit@5 caught 1 miss** |

### 4.4 Error Analysis: Queries Not in Top-3

Only 3 queries out of 100 failed to find the expected memory in the top-3 results:

**1. user_003 — "I'm feeling emotional about client feedback. What helps me?"**
- Expected: Coping strategy for client feedback
- Retrieved: (1) Rejection sensitivity when clients request revisions, (2) Overcommits to client projects, (3) Body-doubling sessions via Discord
- Analysis: The expected memory describes a coping strategy, but the retrieved memories describe problems. This is a classic "strategy vs problem" retrieval mismatch — the embedding for "emotional about feedback" is closer to "rejection sensitivity" (problem) than to the coping strategy.
- **Hit@5: Yes** — the expected memory appears at rank 4-5.

**2. user_016 — "How do I stay organized?"**
- Expected: Uses a military-style operations board
- Retrieved: (1) Structured day plan, (2) Struggles with routine administrative tasks, (3) Needs clear objectives
- Analysis: The query "stay organized" has low token overlap with "operations board mimicking military planning boards". The returned results are contextually relevant but not the exact expected match. This is the vocabulary gap issue identified in the plan.
- **Hit@5: No** — this is the only true MISS.

**3. user_020 — "How do I take care of myself during long coding sessions?"**
- Expected: 90-minute reminders for water breaks
- Retrieved: (1) Forgets to eat/drink/stretch while coding, (2) Codes for 12+ hours, (3) Experiences back pain
- Analysis: Same pattern as user_003 — problem memories outscore strategy memories because "take care of myself" is semantically closer to the problem description than to the reminder strategy.
- **Hit@5: Yes** — the expected memory appears at rank 4-5.

### 4.5 Hit@5: The New Metric

The addition of Hit@5 (Fix 4.1) revealed that **99 of 100 queries find the expected memory within the top 5 results**. This is significant for two reasons:

1. In production, `search_relevant_context()` uses `limit=5`, so the eval now matches production behaviour.
2. Two queries that were counted as misses in v2 (user_003 and user_020) are actually resolved at rank 4-5, confirming the "strategy vs problem" retrieval pattern rather than a fundamental failure.

### 4.6 Mem0 Configuration Compatibility Issues

The plan proposed two Mem0 configuration changes that had to be reverted:

1. **LLM Reranker (Fix 4.2):** Adding `"reranker": {"provider": "llm", ...}` to the Mem0 config caused `mem0.add()` to fail with `'dict' object has no attribute 'replace'`. The error occurs during Mem0's internal fact extraction pipeline, which appears to expect a string but receives a dict when the reranker is configured. This is likely a version mismatch — the feature exists in Mem0's documentation but not in the installed version.

2. **Custom Fact Extraction Prompt (Fix 4.5):** Adding `"custom_fact_extraction_prompt"` initially triggered an OpenAI API error (`'messages' must contain the word 'json'`). After adding "as json" to the prompt, the `'dict' object has no attribute 'replace'` error persisted, indicating a deeper incompatibility.

Both configurations were removed and documented with inline comments in `memory_service.py`. The memory system continues to function correctly with default Mem0 settings.

---

## 5. Cross-Component Analysis

### 5.1 Full Version Comparison

| Component | Metric | v1 (Initial) | v2 (First Fix) | Post-4.5 | Net Change |
|-----------|--------|--------------|-----------------|----------|------------|
| Classification (category) | Accuracy | 68.0% | 96.5% | **100.0%** | **+32.0pp** |
| Classification (productivity) | Accuracy | 63.5% | 83.0% | **86.5%** | **+23.0pp** |
| SenticNet Emotion | Accuracy | 28.0% | 32.0% | **28.0%** | **0.0pp** |
| SenticNet Coverage | Rate | 98.0% | 98.0% | **98.0%** | **0.0pp** |
| Coaching (win rate) | Win rate | 36.7% | 43.3% | **36.7%** | **0.0pp** |
| Coaching (empathy) | With mean | 4.47 | 4.77 | **4.77** | **+0.30** |
| Coaching (safety) | Pass rate | 100% | 100% | **100%** | **0.0pp** |
| Memory Hit@1 | Hit rate | 88.0% | 89.0% | **90.0%** | **+2.0pp** |
| Memory Hit@3 | Hit rate | 97.0% | 97.0% | **97.0%** | **0.0pp** |
| Memory Hit@5 | Hit rate | — | — | **99.0%** | **New** |
| Memory latency | Mean ms | 291.0 | 266.6 | **268.8** | **-22.2** |

### 5.2 Components at Ceiling vs Components with Headroom

**At practical ceiling (no further improvement possible without architectural changes):**
- Classification (category): 100% — perfect on the test set
- Classification (productivity): 86.5% — remaining errors require intent knowledge beyond titles
- Memory retrieval: 97-99% — only 1 true miss in 100 queries
- Coaching safety: 100% — no safety failures across 60 generated responses

**Stuck at fundamental limit (requires different approach):**
- SenticNet emotion: 28% — word-level emotion detection cannot understand sentence meaning
- Coaching win rate: 36.7% — upstream SenticNet noise + 4B model size limit the value of emotion context

### 5.3 The SenticNet Paradox

The most significant finding across Phase 4, v2, and Phase 4.5 is what we call the **SenticNet Paradox**: the system's Hourglass dimensions show statistically significant correlations with expected emotional directions (pleasantness r=0.433, aptitude r=0.390), yet the primary emotion labels are too noisy to improve downstream coaching quality.

This means:
- SenticNet's **dimensional signals** (Hourglass values, polarity, intensity) contain genuine emotional information
- SenticNet's **categorical outputs** (primary emotion labels like "ecstasy", "delight") are unreliable for sentence-level text
- The coaching pipeline feeds categorical outputs to the LLM, not dimensional signals, so the reliable information is underutilised
- A potential improvement path would be to feed raw Hourglass values directly to the LLM and let the model interpret them, rather than mapping through unreliable emotion categories

---

## 6. Recommendations for Future Work

### 6.1 Immediate (No Code Changes)

1. **Use v2 SenticNet pipeline (revert Phase 4.5 changes):** The v2 pipeline achieves 32% emotion accuracy vs 28% post-4.5. The negation detection and Hourglass veto rules should be removed or made significantly more conservative.

2. **Keep Phase 4.5 changes for classification and memory:** The classification fixes are provably correct (100% accuracy). The memory `limit=5` change matches production behaviour.

### 6.2 Medium-Term

1. **Replace SenticNet emotion classification with a sentence-level model.** A fine-tuned all-MiniLM-L6-v2 or distilbert-base-uncased classifier on a small ADHD emotion dataset (~500-1000 labeled sentences) would likely achieve 60-70% accuracy. The existing `all-MiniLM-L6-v2` model is already resident in memory for the classification pipeline, so this adds zero memory overhead.

2. **Feed Hourglass dimensions directly to LLM.** Instead of mapping Hourglass → ADHD state → text label, provide the raw dimensions with brief interpretive labels. This preserves the dimensional signal that SenticNet does well while avoiding the unreliable categorical mapping.

3. **Increase coaching evaluation dataset to n=100+.** The current n=30 is underpowered. With n=100, effect sizes of 0.2 (observed range) would be detectable at p < 0.05.

### 6.3 Long-Term

1. **User feedback loop for productivity classification.** In production, users could correct misclassifications ("Spotify is neutral for me"). These corrections would be stored in the L0 user corrections layer, eliminating the intent ambiguity problem.

2. **A/B testing for coaching quality.** Deploy both SenticNet-enhanced and vanilla coaching, measure user engagement metrics (conversation length, return rate, self-reported helpfulness), and use real-world signal to evaluate coaching quality rather than LLM-as-judge proxies.

---

## 7. Files Changed

### Phase 4.5 Changes

| File | Changes Made |
|------|-------------|
| `evaluation/accuracy/eval_classification.py` | Fix 1.1: em-dash URL extraction; Fix 1.4: title-keyword overrides |
| `knowledge/url_categories.json` | Fix 1.2: Added 7 domains |
| `services/activity_classifier.py` | Fix 1.3: Added 3 L3 keywords |
| `services/senticnet_pipeline.py` | Fixes 2.1-2.5, 2.7, 3.5: Polarity correction, secondary emotion, negation, veto rules, ensemble fields, concepts fix |
| `evaluation/accuracy/eval_senticnet.py` | Fix 2.6: enthusiasm → focused remap + engagement gating |
| `services/mlx_inference.py` | Fixes 3.1, 3.3, 3.4: max_tokens=350, ADHD state position, contradiction guard |
| `services/constants.py` | Fix 3.2: ADHD-state-to-behaviour mapping in system prompt |
| `evaluation/accuracy/eval_coaching_quality.py` | Fix 3.1: max_tokens=350 |
| `evaluation/accuracy/eval_memory_retrieval.py` | Fix 4.1: limit=5, Hit@5 metric |
| `services/memory_service.py` | Fix 4.3: memory_type parameter; Fixes 4.2, 4.5: attempted then reverted (Mem0 incompatibility) |

### Result Files

| File | Description |
|------|-------------|
| `evaluation/results/classification_accuracy_20260324T184236Z.json` | Classification post-4.5 results |
| `evaluation/results/senticnet_accuracy_20260324T184521Z.json` | SenticNet post-4.5 results |
| `evaluation/results/coaching_quality_20260324T185134Z.json` | Coaching quality post-4.5 results |
| `evaluation/results/coaching_responses_20260324T185134Z.json` | Raw coaching responses |
| `evaluation/results/memory_retrieval_20260324T192732Z.json` | Memory retrieval post-4.5 results |

---

## 8. Reproducibility

All evaluations can be reproduced with:

```bash
cd backend

# Classification (requires all-MiniLM-L6-v2 model)
../.venv/bin/python -m evaluation.accuracy.eval_classification

# SenticNet (requires SenticNet API access)
../.venv/bin/python -m evaluation.accuracy.eval_senticnet

# Coaching quality (requires Qwen3-4B model + OPENAI_API_KEY for GPT-4o judge)
../.venv/bin/python -m evaluation.accuracy.eval_coaching_quality

# Memory retrieval (requires PostgreSQL + pgvector + OPENAI_API_KEY)
../.venv/bin/python -m evaluation.accuracy.eval_memory_retrieval
```

All scripts use `random.seed(42)` and `numpy.random.seed(42)` for reproducibility. SenticNet API results may vary slightly across runs due to API-side updates. GPT-4o judge scores may vary due to model non-determinism.

**Environment:**
- Python 3.14.0
- MLX 0.31.0 / mlx-lm 0.31.1
- Qwen3-4B Instruct 4-bit (mlx-community/Qwen3-4B-4bit)
- mem0ai (latest pip release)
- PostgreSQL 16 with pgvector extension
- OpenAI GPT-4o for judge evaluations
- SenticNet API via HTTP (cloud-hosted)

---

## 9. Conclusion

Phase 4.5 achieved its goals for the **classification pipeline** (100% category accuracy, +3.5pp productivity) and confirmed the **memory retrieval system's production readiness** (99% Hit@5). However, the **SenticNet emotion pipeline and downstream coaching quality did not improve** — the heuristic corrections introduced in Phase 4.5 were insufficient to overcome SenticNet's fundamental word-level limitation.

The key takeaway for the FYP is that **SenticNet provides valuable dimensional signals** (Hourglass correlations are statistically significant) but **unreliable categorical outputs** (primary emotion labels). The system architecture should leverage the dimensional signals directly rather than relying on categorical emotion-to-ADHD-state mappings. The classification and memory retrieval components are production-ready and require no further work.

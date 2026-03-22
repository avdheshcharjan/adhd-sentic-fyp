# Phase 1: Smoke Tests — Verify Every Pipeline Component

## Context

Read `00-common.md` first for conventions, dependencies, and file references.

**Goal:** Confirm each component functions correctly in isolation before we measure anything. All tests go in `tests/`. Run with `pytest tests/ -v --timeout=300`.

**Stop rule:** Fix ALL failures before proceeding to Phase 2. Benchmarks on broken components are meaningless.

---

## Task 1.1: SenticNet Service Smoke Test

**File:** `tests/test_senticnet_service.py`

Find the existing SenticNet service in `services/` and test its actual interface.

```
Test 1: Basic concept lookup
  - Input: "happy" → should return polarity > 0, non-empty mood tags
  - Input: "frustrated" → should return polarity < 0
  - Input: "xyznonword123" → should handle gracefully (return None or neutral defaults)

Test 2: Full text analysis
  - Input: "I'm feeling really overwhelmed with my assignments today"
  - Assert: returns a dict with keys: polarity, mood_tags, pleasantness, attention, sensitivity, aptitude
  - Assert: all Hourglass dimension values are floats in range [-1.0, 1.0]
  - Assert: response latency < 2000ms

Test 3: Empty/edge case handling
  - Input: "" (empty string) → should not crash
  - Input: "😀🎉" (emoji only) → should handle gracefully
  - Input: Very long string (5000 chars) → should not hang

Test 4: API resilience
  - Mock the SenticNet API to return 500 → service should return None/defaults, not crash
  - Mock network timeout → service should return None/defaults within timeout period
```

---

## Task 1.2: MLX LLM Service Smoke Test

**File:** `tests/test_mlx_service.py`

Test the on-device Qwen3-4B via MLX. This is the most critical component.

```
Test 1: Model loading
  - Call the load method
  - Assert: model loads without error
  - Measure and print: load time in seconds (expect ~2s on M4)
  - Assert: after loading, memory increased (use psutil)

Test 2: Basic generation
  - Input: simple prompt "Hello, how are you?"
  - Assert: returns non-empty string
  - Assert: response is coherent English (not garbage tokens)
  - Measure and print: time-to-first-token, total generation time, tokens generated

Test 3: Coaching-style generation
  - Input: ADHD coaching system prompt + "I can't focus on my work today, I keep getting distracted"
  - Assert: response mentions focus/distraction/strategies (basic relevance check)
  - Assert: response length 50–500 tokens
  - Assert: no harmful/crisis content in response

Test 4: Thinking mode toggle (Qwen3 feature)
  - Same prompt with /think mode → expect longer, more deliberate response
  - Same prompt with /no_think mode → expect faster, shorter response
  - Print both response times for comparison

Test 5: Auto-unload behavior
  - Load model, generate one response, then trigger unload (or temporarily set TTL to 5s)
  - Assert: memory drops back to near pre-load levels

Test 6: Concurrent requests
  - Fire 3 generation requests via asyncio.gather()
  - Assert: all complete without errors (should queue, not crash)
```

**Note:** If the LLM model isn't downloaded yet, the first run will download Qwen3-4B. This may take several minutes. Use `mlx_lm.convert` or the mlx-community HuggingFace repo.

Run with: `pytest tests/test_mlx_service.py -v --timeout=300`

---

## Task 1.3: Sentence Embedding Service Smoke Test

**File:** `tests/test_embedding_service.py`

Test the all-MiniLM-L6-v2 model used for zero-shot classification.

```
Test 1: Model loading
  - Load the model
  - Assert: loads successfully
  - Measure: load time (expect < 3s), memory footprint (expect ~80-100MB)

Test 2: Embedding generation
  - Input: "Visual Studio Code - main.py"
  - Assert: returns numpy array / list of floats
  - Assert: embedding dimension is 384 (MiniLM-L6-v2 output size)
  - Measure: embedding time per title (expect < 50ms)

Test 3: Cosine similarity sanity check
  - similarity("Visual Studio Code", "productive work") → expect HIGH (> 0.3)
  - similarity("YouTube - funny cats", "productive work") → expect LOW (< 0.2)
  - similarity("YouTube - python tutorial", "productive work") → expect MEDIUM
  - Assert: productive sim > youtube-cats sim

Test 4: Batch performance
  - Embed 100 window titles
  - Measure: total time, average per title
  - Assert: average < 50ms per title
```

---

## Task 1.4: Window Title Classification Cascade Test

**File:** `tests/test_classification_cascade.py`

Test the full 3-tier cascade: rules → embeddings → user cache.

```
Test 1: Rule-based classifier (Tier 1)
  - "Visual Studio Code - project.py" → productive
  - "Slack - #general" → neutral or productive (check your rules)
  - "YouTube - music" → distracting or neutral
  - "reddit.com" → distracting
  - "Google Docs - FYP Report" → productive
  - Measure: classification time per title (expect < 1ms)
  - Print: which tier handled each

Test 2: Zero-shot embedding classifier (Tier 2)
  - Use titles that DON'T match any rules
  - "Obsidian - Meeting Notes" → should classify as productive
  - "TikTok" → should classify as distracting
  - "Calculator" → should classify as neutral
  - Measure: time per title (expect < 50ms)

Test 3: User correction cache (Tier 3)
  - Classify "Discord - study group" → note initial classification
  - Add correction: "Discord - study group" → productive
  - Re-classify → should now return productive from cache
  - Measure: cache lookup time (expect < 1ms)

Test 4: Full cascade integration
  - Feed 50 diverse window titles through cascade
  - Print: tier breakdown (% handled by rules, embeddings, cache)
  - Target: rules handle ≥ 40%
```

---

## Task 1.5: Mem0 Memory Service Smoke Test

**File:** `tests/test_memory_service.py`

```
Test 1: Store and retrieve
  - Store: "User prefers short task lists with max 3 items"
  - Query: "task list preferences" → should return stored memory
  - Assert: retrieved memory contains stored content

Test 2: Contextual retrieval
  - Store 5 memories about different topics
  - Query a specific topic → should return most relevant, not all
  - Measure: retrieval latency (expect < 500ms)

Test 3: Memory metadata
  - Store memory with metadata (emotions, app context)
  - Retrieve and verify metadata is preserved

Test 4: Memory capacity
  - Store 50 memories
  - Verify retrieval still works and returns relevant results
  - Measure: retrieval latency at 50 vs 5 memories
```

---

## Task 1.6: Safety Pipeline Smoke Test

**File:** `tests/test_safety_pipeline.py`

```
Test 1: Crisis keyword detection
  - "I want to hurt myself" → should trigger crisis response
  - "I'm struggling with focus" → should NOT trigger
  - Assert: crisis response includes helpline resources

Test 2: Output safety filter
  - Normal coaching response → should pass unchanged
  - Response with harmful advice → should be filtered/replaced

Test 3: Edge cases
  - "studying the effects of self-harm prevention" → should NOT trigger (academic context)
  - "help" → should not crash
```

---

## Task 1.7: Full Pipeline Integration Test

**File:** `tests/test_full_pipeline.py`

Test the complete ChatProcessor end-to-end.

```
Test 1: Happy path
  - Send: "I've been staring at my screen for 20 minutes and can't start writing my report"
  - Assert: response is non-empty, relevant to ADHD/focus
  - Assert: emotion data returned (pleasantness, attention, sensitivity, aptitude)
  - Measure: total pipeline latency (expect < 10s cold, < 5s warm)

Test 2: Ablation mode
  - Enable ABLATION_MODE=True
  - Send same message
  - Assert: response still generated (pipeline works without SenticNet)
  - Assert: emotion fields are null/empty
  - Measure: pipeline latency without SenticNet

Test 3: Pipeline with screen context
  - Mock screen monitor: app="YouTube", status="distracting"
  - Send: "what should I be doing right now?"
  - Assert: response acknowledges distraction context

Test 4: Graceful degradation
  - Mock SenticNet API as down → pipeline should still return LLM response
  - Mock Mem0 as empty → pipeline should still work with no memory context
```

---

## Completion Criteria

Run: `pytest tests/ -v --timeout=300`

All tests must pass. Print a summary of any component that fails and why. Only proceed to Phase 2 when everything is green.

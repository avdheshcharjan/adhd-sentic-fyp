# Phase 3: System Performance Benchmarks

## Context

Read `00-common.md` first. Phases 1 (smoke tests) and 2 (test data) must be complete.

**Goal:** Measure system performance for every pipeline component and the full end-to-end pipeline. All benchmark files go in `evaluation/benchmarks/`. Results are saved as JSON in `evaluation/results/`.

---

## Task 3.1: Benchmark Runner

**File:** `evaluation/benchmarks/runner.py`

A single entry point that runs all or specific benchmarks.

```python
"""
ADHD Second Brain Pipeline Benchmark Runner

Usage:
    python -m evaluation.benchmarks.runner --all
    python -m evaluation.benchmarks.runner --component llm
    python -m evaluation.benchmarks.runner --component classification
    python -m evaluation.benchmarks.runner --component senticnet
    python -m evaluation.benchmarks.runner --component memory
    python -m evaluation.benchmarks.runner --component pipeline
    python -m evaluation.benchmarks.runner --component energy
"""
```

The runner should:
1. Collect system info: macOS version, chip, RAM, Python version, MLX version, model versions
2. Run the requested benchmarks
3. Save each result as `evaluation/results/benchmark_{component}_{timestamp}.json`
4. Print a human-readable summary table to stdout

Each result JSON should include:
```json
{
  "component": "llm",
  "timestamp": "2026-03-22T14:30:00Z",
  "system_info": {
    "os": "macOS 15.x",
    "chip": "Apple M4",
    "ram_gb": 16,
    "python": "3.11.x",
    "mlx_version": "x.x.x"
  },
  "metrics": { ... },
  "raw_measurements": [ ... ]
}
```

---

## Task 3.2: LLM Inference Benchmarks

**File:** `evaluation/benchmarks/bench_llm.py`

Measure Qwen3-4B performance. Run **30 iterations** (discard first 3 as warmup) for each metric.

**Test prompts (use these exact strings for reproducibility):**

```python
PROMPTS = {
    "short": "I can't focus today",
    "medium": (
        "I've been trying to work on my report for the past hour but I keep "
        "checking social media. I feel guilty about it but can't seem to stop. "
        "What should I do?"
    ),
    "long": (
        "I'm a university student with ADHD. Today I need to finish a 3000-word "
        "essay that's due tomorrow, attend two online lectures, reply to emails "
        "from my supervisor, and prepare for a group presentation on Friday. I'm "
        "feeling completely overwhelmed and don't know where to start. I've already "
        "wasted most of the morning scrolling on my phone. My medication is making "
        "me feel jittery but not actually helping me focus. Can you help me figure "
        "out what to do first?"
    ),
}
```

**Metrics:**

1. **Cold start time** — time from load() call to model ready
   - 5 measurements (full unload between each)
   - Report: mean, median, min, max, stdev

2. **Time-to-first-token (TTFT)** — time from prompt submission to first token
   - 30 iterations per prompt length (short/medium/long)
   - Report: mean, median, p50, p95, p99 per prompt length

3. **Generation throughput (tokens/second)**
   - 30 iterations per prompt
   - Report: tok/s mean, median, min, max per prompt length

4. **Peak memory usage**
   - Measure RSS via psutil at: baseline → after load → during generation → after unload
   - Report: delta for each transition
   - Expected: ~2.3GB for Qwen3-4B q4

5. **Thinking mode comparison**
   - Medium prompt, /think vs /no_think, 10 iterations each
   - Report: TTFT, total time, tokens generated for each mode

---

## Task 3.3: Classification Cascade Benchmarks

**File:** `evaluation/benchmarks/bench_classification.py`

Uses `evaluation/data/window_titles_200.json`.

**Metrics:**

1. **Per-tier latency**
   - Separate 100 titles that hit rules vs embeddings vs cache
   - 100 iterations per tier
   - Report: mean, median, p95 per tier

2. **Tier coverage**
   - Run all 200 titles through the cascade
   - Report: count and % handled by each tier
   - Target: rules ≥ 40%

3. **Embedding model memory footprint**
   - RSS before and after loading MiniLM
   - Report: delta (expect ~80-100MB)

4. **Batch throughput**
   - Classify 1000 titles sequentially (loop the 200-title dataset 5x)
   - Report: total time, titles/second
   - Target: > 100 titles/sec

---

## Task 3.4: SenticNet API Benchmarks

**File:** `evaluation/benchmarks/bench_senticnet.py`

**Metrics:**

1. **Single concept lookup latency**
   - 50 individual concept lookups
   - Report: mean, median, p95, p99

2. **Full text analysis latency by input length**
   - 30 inputs varying: 10, 50, 100, 200 words
   - Report: latency vs input word count (table)

3. **Cache performance** (if SenticNet caching is implemented)
   - Same input, first call vs second call
   - Report: uncached vs cached latency

4. **API reliability**
   - 100 requests, count successes/failures
   - Report: success rate, failure types

5. **Hourglass dimension distribution**
   - Use 50 sentences from `emotion_test_sentences.json`
   - Report: mean, stdev, min, max for each of the 4 dimensions
   - This validates the dimensions actually vary for ADHD text (not all clustered near 0)

---

## Task 3.5: Mem0 Memory Benchmarks

**File:** `evaluation/benchmarks/bench_memory.py`

**Metrics:**

1. **Store latency**
   - Store 100 memories, measure per-store time
   - Report: mean, median, p95

2. **Retrieval latency scaling**
   - Store N memories (N = 10, 50, 100, 200)
   - At each N, run 10 retrieval queries
   - Report: mean retrieval latency at each N (table)

3. **Retrieval relevance quick check**
   - Store 20 memories, query with 10 known-answer queries
   - Report: top-1 hit rate (% where expected memory is rank 1)
   - Target: ≥ 80%

4. **Memory footprint scaling**
   - Measure RSS at 0, 50, 100, 200 stored memories
   - Report: memory growth per stored memory (MB)

---

## Task 3.6: Full Pipeline End-to-End Benchmarks

**File:** `evaluation/benchmarks/bench_pipeline.py`

**Metrics:**

1. **Latency waterfall** — 20 representative messages, measure per-stage time:
   ```
   a. SenticNet analysis:     ___ ms
   b. Safety input check:     ___ ms
   c. Mem0 retrieval:         ___ ms
   d. Screen context fetch:   ___ ms
   e. Prompt assembly:        ___ ms
   f. LLM model load (cold):  ___ ms  (0 if warm)
   g. LLM TTFT:               ___ ms
   h. LLM generation:         ___ ms
   i. Safety output check:    ___ ms
   j. Mem0 store:             ___ ms
   k. TOTAL:                  ___ ms
   ```
   Report: mean waterfall across 20 messages. Identify the bottleneck stage.

2. **Warm vs cold latency**
   - Cold: model not loaded, first request
   - Warm: model loaded, subsequent request
   - Report: cold total, warm total, delta

3. **Ablation timing**
   - Same 20 messages with ABLATION_MODE=False, then ABLATION_MODE=True
   - Report: mean latency each, delta (= performance cost of SenticNet layer)

4. **System resources during burst**
   - Sample CPU% and RSS every 500ms during 10 back-to-back chat messages
   - Report: peak CPU%, peak memory, average CPU%, average memory
   - Target: peak memory < 6GB

5. **Concurrent stress test**
   - Fire 5 simultaneous chat requests
   - Assert: all complete
   - Report: mean and max latency under load

---

## Task 3.7: Energy Benchmark (Optional)

**File:** `evaluation/benchmarks/bench_energy.py`

Try to install `zeus-apple-silicon` (`pip install zeus-apple-silicon --break-system-packages`). If it works:

1. **Energy per inference** — CPU, GPU, DRAM energy in mJ for 20 inferences
2. **Idle power** — watts with app running but no inference
3. **Battery impact estimate** — (energy per inference × inferences per hour) / battery capacity

If `zeus-apple-silicon` is not available, try `powermetrics` (requires sudo):
```bash
sudo powermetrics --samplers cpu_power,gpu_power -i 1000 -n 30
```

If neither works, use `psutil.sensors_battery()` to measure battery drain over 100 inferences.

If nothing works, skip this task and note it as a limitation.

---

## Completion Criteria

```bash
python -m evaluation.benchmarks.runner --all
```

Should produce JSON files in `evaluation/results/`:
- `benchmark_llm_{timestamp}.json`
- `benchmark_classification_{timestamp}.json`
- `benchmark_senticnet_{timestamp}.json`
- `benchmark_memory_{timestamp}.json`
- `benchmark_pipeline_{timestamp}.json`
- `benchmark_energy_{timestamp}.json` (if available)

And print a summary table to stdout with all key metrics.

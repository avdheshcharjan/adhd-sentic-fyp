# Phase 5: Evaluation Logger & Results Aggregator

## Context

Read `00-common.md` first. Phases 3 (benchmarks) and 4 (accuracy) must be complete so there are results to aggregate.

**Goal:** Two things: (1) Wire an evaluation logger into the live ChatProcessor so future interactions are recorded, and (2) build a results aggregator that combines all benchmark and accuracy results into a single summary.

---

## Task 5.1: Enhanced Evaluation Logger

**File:** `services/evaluation_logger.py`

This extends Change 2 from `rui-mao-feedback-code-changes.md` with additional fields discovered during benchmarking.

```python
"""
Enhanced evaluation logger for the ADHD Second Brain pipeline.

Captures per-interaction metrics in JSONL format for:
- Ablation analysis (with vs without SenticNet)
- Persona simulation analysis
- Within-subjects study data collection
- Post-hoc performance analysis

Log format: JSONL (one JSON object per line)
Load with: pandas.read_json(path, lines=True)

Enabled when settings.EVALUATION_LOGGING = True.
"""
```

**Fields to log per interaction:**

```python
class EvaluationLogEntry(BaseModel):
    # Identity
    timestamp: str                          # ISO 8601
    conversation_id: str
    session_id: str                         # Groups interactions within one eval session
    ablation_mode: bool                     # True = SenticNet disabled
    persona_id: Optional[str] = None        # Set during LLM persona simulation

    # Input
    user_message: str
    user_message_length: int                # char count
    user_message_word_count: int

    # SenticNet output (all null when ablation_mode=True)
    sentic_polarity: Optional[float] = None
    sentic_mood_tags: Optional[list[str]] = None
    hourglass_pleasantness: Optional[float] = None
    hourglass_attention: Optional[float] = None
    hourglass_sensitivity: Optional[float] = None
    hourglass_aptitude: Optional[float] = None
    sentic_latency_ms: Optional[float] = None

    # Classification context (if screen monitor active)
    active_app: Optional[str] = None
    active_title: Optional[str] = None
    classification_result: Optional[str] = None     # productive/neutral/distracting
    classification_tier: Optional[str] = None       # rules/embeddings/cache
    classification_confidence: Optional[float] = None
    classification_latency_ms: Optional[float] = None

    # Memory context
    memories_retrieved_count: int = 0
    memory_retrieval_latency_ms: Optional[float] = None

    # LLM output
    llm_response: str = ""
    llm_response_length: int = 0
    llm_response_token_count: int = 0
    llm_ttft_ms: Optional[float] = None
    llm_generation_ms: Optional[float] = None
    llm_tokens_per_second: Optional[float] = None
    llm_thinking_mode: Optional[str] = None         # "think" or "no_think"

    # Pipeline totals
    pipeline_total_ms: float = 0.0
    safety_input_triggered: bool = False
    safety_output_triggered: bool = False

    # System state snapshot
    system_memory_rss_mb: Optional[float] = None
    system_cpu_percent: Optional[float] = None
```

**Logger implementation:**

```python
class EvaluationLogger:
    def __init__(self, log_dir: str = "data/evaluation_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    async def log(self, entry: EvaluationLogEntry) -> None:
        """Append entry as JSON line. Fire-and-forget safe."""
        filename = f"{entry.session_id}.jsonl"
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def load_session(self, session_id: str) -> list[EvaluationLogEntry]:
        """Load all entries for a session."""
        filepath = os.path.join(self.log_dir, f"{session_id}.jsonl")
        entries = []
        with open(filepath, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(EvaluationLogEntry.model_validate_json(line.strip()))
        return entries

    def load_all(self) -> list[EvaluationLogEntry]:
        """Load all entries across all sessions."""
        entries = []
        for f in sorted(os.listdir(self.log_dir)):
            if f.endswith(".jsonl"):
                session_id = f.replace(".jsonl", "")
                entries.extend(self.load_session(session_id))
        return entries
```

---

## Task 5.2: Wire Logger into ChatProcessor

Modify the existing `ChatProcessor.process_message()` (or equivalent):

1. Wrap each pipeline stage with `time.perf_counter()` timing
2. Collect all timings and outputs into an `EvaluationLogEntry`
3. At the end of processing, fire-and-forget the log write:
   ```python
   if settings.EVALUATION_LOGGING:
       asyncio.create_task(self.eval_logger.log(entry))
   ```
4. Capture system state via psutil:
   ```python
   import psutil
   process = psutil.Process()
   entry.system_memory_rss_mb = process.memory_info().rss / (1024 * 1024)
   entry.system_cpu_percent = process.cpu_percent(interval=None)
   ```

**Critical:** The logger must NOT add noticeable latency. The `asyncio.create_task()` fire-and-forget pattern ensures the log write doesn't block the response.

**Test the wiring:**
- Enable `EVALUATION_LOGGING=True`
- Send 5 chat messages through the pipeline
- Verify JSONL file appears in `data/evaluation_logs/`
- Load with pandas and verify all fields are populated:
  ```python
  import pandas as pd
  df = pd.read_json("data/evaluation_logs/{session}.jsonl", lines=True)
  print(df.columns.tolist())
  print(df[["pipeline_total_ms", "llm_generation_ms", "sentic_latency_ms"]].describe())
  ```

---

## Task 5.3: Results Aggregator

**File:** `evaluation/aggregate_results.py`

```python
"""
Aggregate all evaluation results into a single summary.

Reads JSON files from evaluation/results/ and produces:
1. Formatted console summary
2. JSON summary: evaluation/results/summary_{timestamp}.json
3. Markdown summary: evaluation/results/summary_{timestamp}.md
   (structured to paste into FYP report Chapter 5)

Usage:
    python -m evaluation.aggregate_results
"""
```

**The aggregator should:**

1. Scan `evaluation/results/` for all `benchmark_*.json` and `*_accuracy_*.json` files
2. Extract key metrics from each
3. Produce this console output:

```
================================================================
  ADHD Second Brain Pipeline — Evaluation Summary
  Date: 2026-03-22 | Hardware: Apple M4, 16GB
================================================================

SYSTEM PERFORMANCE
──────────────────────────────────────────────────────
  LLM cold start:          {mean:.1f}s ± {std:.1f}s
  LLM TTFT (warm):         {mean:.0f}ms (p95: {p95:.0f}ms)
  LLM generation:          {mean:.0f} tok/s
  LLM peak memory:         {peak:.1f}GB
  Classification latency:  {mean:.1f}ms (p95: {p95:.1f}ms)
  SenticNet latency:       {mean:.0f}ms
  Mem0 retrieval:          {mean:.0f}ms
  Pipeline total (warm):   {mean:.1f}s (p95: {p95:.1f}s)
  Pipeline total (cold):   {mean:.1f}s
  Peak system memory:      {peak:.1f}GB / 16GB

ML ACCURACY
──────────────────────────────────────────────────────
  Classification macro-F1:   {f1:.3f}
    Productive:   P={p:.2f}  R={r:.2f}  F1={f1:.2f}
    Neutral:      P={p:.2f}  R={r:.2f}  F1={f1:.2f}
    Distracting:  P={p:.2f}  R={r:.2f}  F1={f1:.2f}

  Coaching quality (1-5):
    Empathy:              {mean:.2f} ± {std:.2f}
    Helpfulness:          {mean:.2f} ± {std:.2f}
    ADHD-appropriateness: {mean:.2f} ± {std:.2f}
    Coherence:            {mean:.2f} ± {std:.2f}
    Informativeness:      {mean:.2f} ± {std:.2f}

  SenticNet ablation (win/tie/loss):
    With SenticNet wins:  {n}/{total} ({pct:.0f}%)
    Ties:                 {n}/{total} ({pct:.0f}%)
    Without wins:         {n}/{total} ({pct:.0f}%)
    Wilcoxon p-value:     {p:.4f}

  Emotion detection macro-F1:  {f1:.3f}
  Hourglass correlations:
    Pleasantness: r={r:.3f} (p={p:.4f})
    Attention:    r={r:.3f} (p={p:.4f})
    Sensitivity:  r={r:.3f} (p={p:.4f})
    Aptitude:     r={r:.3f} (p={p:.4f})

  Memory retrieval:
    Hit@1: {pct:.0f}%
    Hit@3: {pct:.0f}%
    nDCG@3: {score:.3f}
================================================================
```

4. Save the same data as JSON and markdown

**For the markdown output**, structure it with sections that map to FYP Chapter 5:
- "5.3 LLM Performance Evaluation" → LLM benchmarks
- "5.4 Sentiment Analysis Accuracy" → SenticNet metrics + ablation
- "5.5 Distraction Detection Accuracy" → classification metrics
- "5.6 System Resource Usage" → memory, CPU, battery
- "5.7 Results Discussion" → comparison, bottleneck analysis

**Handle missing results gracefully.** If a benchmark didn't run, show "N/A" instead of crashing.

---

## Completion Criteria

1. `services/evaluation_logger.py` exists and is importable
2. ChatProcessor logs interactions when `EVALUATION_LOGGING=True`
3. Running `python -m evaluation.aggregate_results` produces:
   - Console output with all available metrics
   - `evaluation/results/summary_{timestamp}.json`
   - `evaluation/results/summary_{timestamp}.md`
4. The markdown output is structured for direct use in the FYP report

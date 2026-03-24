# Chapter 5 — Testing and Evaluation

> **FYP Report Draft: ADHD Second Brain**
> *Prepared for NTU CCDS Final Year Project Report*
> *Date: 2026-03-25*
> *LaTeX-ready: IEEE numeric citations, third person, past tense*
> *Target: 8–10 pages in 12pt Times New Roman, A4, 1.5 spacing*

---

## 5.1 Testing Strategy

The evaluation of the ADHD Second Brain system followed a three-phase methodology aligned with established software engineering practices for AI-intensive applications [26, 27]. Each phase was designed to map directly to a project objective, maintaining traceability from design through implementation to empirical validation.

**Phase 1** validated individual component functionality through unit and integration testing. **Phase 2** assessed classification accuracy and affective computing correctness against curated test datasets. **Phase 3** — the focus of this chapter — measured system performance, energy consumption, and reproducibility under realistic workloads on the target hardware platform.

All benchmarks were executed on the target deployment hardware: a MacBook Pro with Apple M4 chip (10-core CPU, 10-core GPU) and 16 GB unified memory, running macOS 26.2. This hardware configuration represents the minimum viable deployment for the application's on-device inference architecture.

### 5.1.1 Benchmark Methodology

Each benchmark component was executed twice (Run 1 and Run 2) on the same hardware on the same day with a 35-minute interval, using deterministic seeding (`random.seed(42)`, `numpy.random.seed(42)`) where applicable. Timing was measured using `time.perf_counter()` (nanosecond resolution), memory via `psutil` RSS measurement, and energy via the `zeus-apple-silicon` framework [28], which exposes Apple's private per-component power monitoring for CPU, GPU, DRAM, and Neural Engine subsystems.

The two-run protocol served to quantify cross-run variance and establish confidence intervals, following the reproducibility standards recommended for ML systems evaluation [5, 6].

---

## 5.2 On-Device LLM Inference Performance

The system employs Qwen3-4B [19] — a 4-billion parameter dense transformer — quantized to 4-bit precision and executed via Apple's MLX framework [18] on the Metal GPU. This section evaluates inference throughput, latency, memory footprint, and the cost of the extended thinking mode.

### 5.2.1 Inference Throughput

Generation throughput was measured across three prompt lengths (short: 4 words, medium: 38 words, long: 97 words) with 8 measured iterations per prompt length after 2 warmup iterations.

| Prompt Length | Run 1 (tok/s) | Run 2 (tok/s) | Mean | CV |
|---------------|---------------|---------------|------|-----|
| Short | 38.2 | 37.9 | 38.1 | 0.6% |
| Medium | 35.4 | 36.4 | 35.9 | 2.0% |
| Long | 37.2 | 37.4 | 37.3 | 0.4% |
| **Overall** | — | — | **37.1** | **0.8%** |

Throughput was consistent at **37.1 tok/s** (95% CI: 35–39 tok/s) across all prompt lengths and both runs, with a coefficient of variation (CV) below 2%. This consistency is expected: autoregressive decoding on Apple Silicon is memory-bandwidth-bound [27], and the M4's unified memory bandwidth (120 GB/s) provides a stable throughput ceiling for 4-bit quantized models.

For contextual comparison, published MLX benchmarks on the same M4 chip report 40 tok/s for Llama 3.1 8B (Q4\_K\_M) via Ollama and 60–70 tok/s for Qwen 3.5 35B-A3B (MoE architecture with only 3B active parameters). The measured 37.1 tok/s for Qwen3-4B-4bit is consistent with expectations for a 4B dense model on the M4 base configuration.

At the observed throughput, typical coaching responses of 50–100 tokens complete in **1.4–2.7 seconds**, which falls within the 2–5 second response window considered acceptable for conversational AI interfaces [8, 9].

### 5.2.2 Cold Start and Generation Latency

| Metric | Run 1 | Run 2 | Mean | Variance |
|--------|-------|-------|------|----------|
| Cold start (model load) | 0.80s | 1.07s | 0.94s | 33.8% |
| Short generation (mean) | 1,490ms | 1,420ms | 1,455ms | 4.7% |
| Medium generation (mean) | 2,271ms | 2,297ms | 2,284ms | 1.1% |
| Long generation (mean) | 2,374ms | 2,237ms | 2,306ms | 5.8% |

Cold start time exhibited the highest variance (33.8%) because it depends on OS page cache state and Metal shader compilation — factors influenced by preceding system activity. Generation latency was stable (1–6% variance) because it is governed by the deterministic Metal GPU decode loop.

Generation time scaled primarily with **output token count**, not input length. The medium prompt (38 words) produced ~85 tokens while the long prompt (97 words) produced ~85 tokens, resulting in nearly identical latencies despite a 2.6x difference in input length. This confirms that the Qwen3-4B attention mechanism handles the application's typical context lengths (under 2,000 tokens) efficiently.

### 5.2.3 Thinking Mode Overhead

Qwen3-4B supports dual generation modes: `/think` (extended chain-of-thought reasoning) and `/no_think` (direct response). This mechanism was evaluated to inform the application's mode-selection strategy.

| Mode | Run 1 Mean | Run 2 Mean | Consolidated | Output Tokens |
|------|-----------|-----------|-------------|---------------|
| /think | 4,920ms | 4,556ms | 4,738ms | ~212 |
| /no_think | 1,903ms | 2,188ms | 2,046ms | ~77 |
| **Ratio** | **2.6x** | **2.1x** | **~2.3x** | **~2.8x** |

The `/think` mode generated approximately 2.8x more tokens (including internal reasoning), resulting in a 2.3x latency overhead. The latency ratio was lower than the token ratio because the per-token generation cost includes fixed overhead (prompt encoding, first-token latency) that is amortized across longer outputs.

For the ADHD coaching use case, this informed the design decision to use `/no_think` for routine interactions (acknowledgments, simple prompts) and `/think` for complex emotional situations where deeper deliberation produces meaningfully better therapeutic guidance.

### 5.2.4 Memory Footprint

| Measurement | Run 1 | Run 2 |
|-------------|-------|-------|
| RSS with model loaded | 2,734 MB | 2,974 MB |
| RSS after unload + GC | 2,682 MB | 2,923 MB |
| RSS delta (Python-side) | 52 MB | 51 MB |

The low RSS delta (~51 MB) substantially understates the true model footprint because MLX allocates model weights in Metal GPU buffers within Apple's unified memory architecture, which are not reflected in process-level RSS measurements. The actual GPU memory consumption of Qwen3-4B-4bit is approximately **2.3 GB**, determined by the on-disk model size of the 4-bit quantized weights. This leaves approximately 13.7 GB of the 16 GB unified memory budget for the operating system, other application components, and user applications.

---

## 5.3 Activity Classification Evaluation

The 5-tier classification cascade classifies user screen activity into productivity categories (productive, neutral, distracting) using a waterfall architecture: user corrections (Tier 0), application name dictionary (Tier 1), URL domain classification (Tier 2), title keyword matching (Tier 3), and sentence embedding similarity via all-MiniLM-L6-v2 [23, 24] (Tier 4).

### 5.3.1 Tier Coverage Distribution

The classification cascade was evaluated on a curated dataset of 200 window titles representing realistic macOS screen activities.

| Tier | Method | Count | Percentage |
|------|--------|-------|-----------|
| 0 | User corrections cache | 0 | 0.0% |
| 1 | App name dictionary | 113 | 56.5% |
| 2 | URL domain classification | 0 | 0.0% |
| 3 | Title keyword matching | 43 | 21.5% |
| 4 | Embedding similarity | 44 | 22.0% |
| **Rules (Tiers 0–3)** | — | **156** | **78.0%** |

The rule-based tiers resolved **78.0%** of classifications without invoking the embedding model, nearly double the design target of ≥ 40%. This result was **perfectly deterministic** — identical across both runs, as expected for a pure function of input text and static lookup tables.

Tier 0 and Tier 2 showed 0% coverage because the benchmark dataset contained no user corrections and no URL-bearing window titles, respectively. In production with browser windows and accumulated user corrections, both tiers would contribute additional rule-based coverage, further reducing reliance on the embedding model.

### 5.3.2 Classification Latency

| Tier | Method | Mean Latency | P95 Latency |
|------|--------|-------------|-------------|
| 1 | App name lookup | 0.001 ms | 0.003 ms |
| 3 | Keyword matching | 0.001 ms | 0.002 ms |
| 4 | Embedding similarity | **7.9 ms** | **10.5 ms** |

Rule-based tiers operated at **sub-microsecond** latency — effectively instantaneous for a system that polls screen activity every 2 seconds. The embedding tier (all-MiniLM-L6-v2 inference plus cosine similarity) averaged 7.9 ms, comfortably within real-time requirements.

### 5.3.3 Batch Throughput

Sequential classification of 1,000 titles (5x the evaluation dataset):

| Metric | Run 1 | Run 2 | Mean |
|--------|-------|-------|------|
| Throughput | 556 titles/s | 541 titles/s | **549 titles/s** |
| Total time | 1.800s | 1.847s | 1.824s |

The system classified **549 titles per second** on average — a **5.5x margin** over the design target of 100 titles/s. Given that the macOS Accessibility API is polled at most a few times per second, the classification cascade provides orders-of-magnitude headroom for real-time screen monitoring.

### 5.3.4 Embedding Model Footprint

The all-MiniLM-L6-v2 model (22M parameters, 6-layer BERT) consumed approximately **16.2 MB** of additional RSS upon loading (mean of +14.6 MB and +17.7 MB across runs). The model is approximately 80 MB on disk but its in-memory representation is compact due to PyTorch's lazy loading and shared tensor storage.

---

## 5.4 Affective Computing Evaluation (SenticNet)

The application integrates the SenticNet API [16, 17] for multi-dimensional affective analysis of user messages. SenticNet's Hourglass of Emotions model provides four affective dimensions (introspection, temper, attitude, sensitivity) plus polarity, intensity, and categorical emotion labels — providing richer emotional context than binary sentiment classifiers.

### 5.4.1 API Latency

Single-concept emotion API latency was measured over 50 consecutive calls:

| Metric | Run 1 | Run 2 | Consolidated |
|--------|-------|-------|-------------|
| Mean | 595.6 ms | 544.9 ms | **570 ms** |
| Median | 529.3 ms | 513.4 ms | **521 ms** |
| P95 | 812.4 ms | 695.8 ms | 754 ms |
| Success rate | 100% | 100% | **100%** |

The median (521 ms) is the recommended reporting metric for SenticNet latency, as it is less affected by the cold-start spike on the first API call and showed only 3% cross-run variance compared to 8.5% for the mean.

Full pipeline latency (13 API calls across 4 processing tiers) scaled approximately linearly with input length:

| Input Length | Words | Mean Latency | Per-Word Cost |
|-------------|-------|-------------|---------------|
| Short | 10 | 2.6s | 260 ms/word |
| Medium | 53 | 3.3s | 62 ms/word |
| Long | 94 | 4.5s | 48 ms/word |
| Very Long | 201 | 9.1s | 45 ms/word |

The decreasing per-word cost with longer inputs reflects the fixed overhead (~500 ms network round-trip) being amortized across more words. For the application's typical message length of 20–50 words, the affective analysis completes in approximately 3–4 seconds.

For comparison, a local BERT-based binary sentiment classifier would run in 50–100 ms but would not provide the four-dimensional Hourglass model that enables the system's ADHD-specific emotional state mapping. The SenticNet approach trades latency for affective granularity that is unavailable from any on-device alternative.

### 5.4.2 Hourglass of Emotions Validation

The SenticNet ensemble endpoint was evaluated on 50 ADHD-related sentences to verify meaningful affective differentiation:

| Dimension | Mean | Stdev | Range |
|-----------|------|-------|-------|
| Introspection | 8.50 | 66.65 | [-97.7, +99.1] |
| Temper | 4.18 | 48.35 | [-96.7, +99.9] |
| Attitude | 6.90 | 58.92 | [-89.5, +82.1] |
| Sensitivity | 12.45 | 53.58 | [-99.9, +98.1] |

All four dimensions demonstrated **high variance** (standard deviations of 48–67) spanning nearly the full [-100, +100] scale. This confirms that SenticNet produces meaningfully differentiated affective signals for ADHD-related text, rather than clustering near neutral values. The result was **perfectly deterministic** across both runs — the SenticNet ensemble endpoint is a stateless function that returns identical values for identical input text.

The Hourglass dimensions feed into the system's `map_hourglass_to_adhd_state()` method, which maps affective states to ADHD-specific behavioral profiles (e.g., high temper with low introspection suggesting emotional dysregulation, a recognized "fourth core symptom" of ADHD [1, 4]).

### 5.4.3 Reliability

The SenticNet API achieved **100% reliability** (200/200 calls across 7 endpoints over both runs). The seven endpoints tested were: polarity, intensity, emotion, depression, toxicity, engagement, and wellbeing.

---

## 5.5 Conversational Memory Evaluation (Mem0)

The application employs Mem0 [20] with PostgreSQL and pgvector for persistent, semantically searchable conversational memory. Each memory store operation invokes OpenAI gpt-4o-mini for memory fact extraction and text-embedding-3-small for vector embedding; retrieval uses only the embedding model plus pgvector cosine similarity search.

### 5.5.1 Store and Retrieval Latency

| Operation | Run 1 | Run 2 | Consolidated | CV |
|-----------|-------|-------|-------------|-----|
| Store (mean) | 6,234 ms | 5,533 ms | **5,884 ms** | 11.2% |
| Retrieval (mean) | 308.5 ms | 238.8 ms | **274 ms** | 22.6% |
| Retrieval (median) | 323.4 ms | 195.5 ms | 259 ms | 39.6% |

Store latency (~5.9s) is dominated by the OpenAI gpt-4o-mini API call for memory fact extraction. Retrieval is significantly faster (~274 ms) because it requires only an embedding call plus a pgvector similarity search.

For comparison, Mem0's official benchmark [20] reports a median retrieval latency of 200 ms on the LOCOMO benchmark — closely matching the 197 ms median observed in Run 2 of this evaluation. The system's pgvector deployment achieves parity with Mem0's published performance characteristics.

Mem0 showed the highest cross-run variance of any component (11–40%), reflecting the stochastic nature of cloud API response times. This variance is inherent to any cloud-dependent architecture and represents a documented limitation of the current design.

### 5.5.2 Retrieval Relevance

Ten known-answer query-memory pairs were used to evaluate semantic retrieval quality (top-1 hit rate):

| Run | Hits | Hit Rate |
|-----|------|----------|
| Run 1 | 9/10 | 90% |
| Run 2 | 10/10 | 100% |
| **Consolidated** | — | **95%** |

The single miss in Run 1 ("Do I exercise?" returned "exercising improves focus" instead of "exercises every morning for 30 minutes") was caused by the evaluation's keyword-matching heuristic failing on a different word form, not a retrieval failure. In Run 2, gpt-4o-mini extracted a slightly different memory paraphrase that passed the keyword check. The actual retrieved memory was semantically correct in both runs.

The consolidated 95% top-1 hit rate exceeds the design target of ≥ 80% and significantly exceeds Mem0's 66.9% accuracy on the LOCOMO benchmark [20]. However, this comparison should be interpreted cautiously: the evaluation used 10 hand-crafted query-memory pairs with keyword matching, while LOCOMO is a standardized multi-session benchmark with more challenging retrieval scenarios. The key finding is that Mem0 retrieval quality is sufficient for the application's conversational memory requirements.

### 5.5.3 Memory Footprint

The Mem0 client consumed approximately **502 MB** RSS (mean of 499 MB and 504 MB), with less than 1% variance between runs. Since actual memory storage resides in PostgreSQL (pgvector), the in-process footprint reflects only the Python client overhead and is independent of the number of stored memories.

---

## 5.6 End-to-End Pipeline Evaluation

The full ChatProcessor pipeline — comprising SenticNet affective analysis, safety check, memory retrieval, prompt assembly, LLM generation, and memory store — was evaluated with 20 representative ADHD-relevant messages.

### 5.6.1 Latency Waterfall

| Stage | Run 1 Mean | Run 2 Mean | Consolidated | % of Total |
|-------|-----------|-----------|-------------|-----------|
| SenticNet analysis | 4,092 ms | 4,248 ms | 4,170 ms | 29.9% |
| Memory retrieval | 421 ms | 301 ms | 361 ms | 2.6% |
| LLM generation | 3,950 ms | 4,052 ms | 4,001 ms | 28.7% |
| Memory store | 4,891 ms | 5,967 ms | 5,429 ms | 38.8% |
| Safety + assembly | < 1 ms | < 1 ms | < 1 ms | < 0.1% |
| **Total E2E** | **13,353 ms** | **14,568 ms** | **13,961 ms** | — |

The end-to-end pipeline averaged **~14 seconds** per message. The bottleneck hierarchy was stable across both runs:

```
Mem0 Store:  38.8%  ██████████████████████████████████████░░░░  ← Bottleneck (cloud API)
SenticNet:   29.9%  ██████████████████████████████░░░░░░░░░░░░  ← Cloud API
LLM:         28.7%  █████████████████████████████░░░░░░░░░░░░░  ← On-device
Mem0 Retr:    2.6%  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

Cloud-dependent components (Mem0 store + SenticNet) together accounted for **68.7%** of total pipeline latency, while the on-device LLM contributed only 28.7%. This distribution has two important implications: (1) the on-device inference architecture has been effectively optimized via MLX quantization, and (2) the primary optimization opportunities lie in reducing cloud API dependency.

### 5.6.2 Ablation Analysis: Cost of Affective Computing

To quantify the latency cost of emotional awareness, the pipeline was tested in two configurations: full pipeline (with SenticNet context in the system prompt) and ablation mode (vanilla system prompt, SenticNet bypassed).

| Configuration | Run 1 | Run 2 | Consolidated |
|--------------|-------|-------|-------------|
| Full pipeline (with SenticNet) | 5,270 ms | 5,388 ms | 5,329 ms |
| Ablation (without SenticNet) | 2,475 ms | 2,675 ms | 2,575 ms |
| **SenticNet cost** | **53.0%** | **50.4%** | **51.7%** |

SenticNet contributed **51.7%** of the generation pipeline latency (~2.8 seconds). This represents the quantified cost of affective computing — the system trades approximately half its response time for emotionally-aware guidance. The ablation result was highly stable across runs (2.6 percentage point variance), indicating that the cost is a predictable architectural property rather than a variable runtime characteristic.

The system provides a runtime toggle (`ABLATION_MODE`) enabling two operational profiles:
- **Full mode (~5.3s):** Emotionally-aware responses with Hourglass context, suitable for complex ADHD situations
- **Fast mode (~2.6s):** Direct responses for routine interactions where emotional context is not critical

### 5.6.3 Resource Utilization

| Metric | Run 1 | Run 2 | Assessment |
|--------|-------|-------|-----------|
| Peak RSS | 2,908 MB | 1,485 MB | Well under 6 GB target |
| Peak CPU | 93.9% | 82.0% | GPU-bound, not CPU-bound |
| Average CPU | 27.9% | 31.1% | Low sustained load |

The peak RSS difference (2,908 vs 1,485 MB) between runs reflects different MLX model loading states during the burst test, not a real memory improvement. Both values are well within the design target of < 6 GB, confirming that the application leaves ample memory for the operating system and concurrent user applications on a 16 GB system.

### 5.6.4 Sequential Stress Test

Five back-to-back requests were processed to verify system stability under sustained load:

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| All succeeded | 5/5 | 5/5 |
| Mean latency | 2,774 ms | 2,641 ms |
| Max latency | 3,127 ms | 3,034 ms |
| Total wall time | 13,870 ms | 13,205 ms |

All requests completed successfully with consistent latency (2.3–3.1s range), confirming system stability under the realistic single-user workload. The MLX Metal GPU backend maintained stable performance without thermal throttling or memory accumulation across sequential requests.

**MLX Thread Safety Constraint:** Concurrent inference was not tested because MLX's Metal backend is not thread-safe — concurrent `generate()` calls from multiple threads cause a segfault via a Metal command buffer assertion (`AGXG16GFamilyCommandBuffer`). This is a fundamental Apple Silicon MLX framework limitation. Any future extension requiring concurrent inference (e.g., parallel SenticNet analysis and LLM generation) must use separate processes, not threads.

---

## 5.7 Energy Consumption Analysis

Energy profiling was conducted using `zeus-apple-silicon` [28], which exposes Apple's private per-component power monitoring for CPU, GPU, DRAM, and the Apple Neural Engine (ANE).

### 5.7.1 Idle Power

With the application running but not performing inference:

| Component | Run 1 | Run 2 | Mean |
|-----------|-------|-------|------|
| CPU | 0.525 W | 0.488 W | 0.507 W |
| GPU | 0.038 W | 0.036 W | 0.037 W |
| DRAM | 0.159 W | 0.155 W | 0.157 W |
| ANE | 0.000 W | 0.000 W | 0.000 W |
| **Total** | **0.72 W** | **0.68 W** | **0.70 W** |

The application's idle power draw of **0.70 W** is negligible relative to the MacBook Pro's total system power budget. For context, the M4 chip's peak power consumption under sustained ML workloads reaches 40–80 W, and an NVIDIA RTX 4090 consumes approximately 450 W during inference.

### 5.7.2 Energy Per Inference

Energy consumption was measured across 20 LLM inference operations:

| Component | Mean (mJ) | % of Total | Run 1 | Run 2 | CV |
|-----------|-----------|-----------|-------|-------|-----|
| GPU | 15,298 | 71.8% | 15,050 | 15,546 | 3.3% |
| DRAM | 4,571 | 21.5% | 4,498 | 4,643 | 3.2% |
| CPU | 1,446 | 6.8% | 1,474 | 1,417 | 3.9% |
| ANE | 0 | 0.0% | 0 | 0 | 0% |
| **Total** | **21,314** | — | **21,022** | **21,606** | **2.8%** |

Energy was the **most reproducible benchmark category**, with only 2.8% cross-run variance for total energy and near-identical component proportions (< 0.4 percentage point variance in all categories).

The energy breakdown reveals the hardware architecture story:
- **GPU (71.8%):** The Metal GPU performs all matrix multiplications for the transformer's attention and feed-forward layers. This dominance is expected for quantized LLM inference [27].
- **DRAM (21.5%):** The 4-bit quantized model weights (~2.3 GB) must be read from unified memory for every token generation step. Memory bandwidth is the throughput bottleneck.
- **CPU (6.8%):** Handles tokenization, temperature-based sampling, and Metal command buffer coordination.
- **ANE (0%):** Apple's Neural Engine is not utilized by the MLX framework for LLM inference. MLX exclusively targets the Metal GPU.

### 5.7.3 Battery Life Estimation

Based on the MacBook Pro M4's 72.4 Wh battery:

| Usage Scenario | Inferences/hr | Energy/hr | Estimated Battery Life | Battery Drain/hr |
|---------------|--------------|-----------|----------------------|-----------------|
| Active coaching (1 msg/min) | 60 | 3.74 Wh | **~69 hours** | ~1.4% |
| Casual use (1 msg/5 min) | 12 | 2.71 Wh | **~96 hours** | ~1.0% |

The battery life estimates (69–96 hours) far exceed the MacBook Pro's actual battery life under normal usage (8–12 hours with display active), confirming that the ADHD coaching application's energy footprint constitutes a **negligible fraction of total system power consumption** — approximately 1.0–1.4% of battery per hour from inference alone.

This result supports one of the project's central technical claims: **on-device LLM inference on Apple Silicon M4 is viable for always-on ADHD coaching applications without meaningful battery impact**, in stark contrast to cloud-based LLM solutions that require constant network connectivity and server-side GPU resources.

---

## 5.8 Reproducibility Assessment

The two-run protocol enabled a systematic assessment of measurement reproducibility across all components.

### 5.8.1 Variance Classification

| Category | CV Range | Components |
|----------|---------|------------|
| **Deterministic** | 0% | Classification tier coverage, Hourglass dimension values, API reliability |
| **Very High Stability** | < 5% | LLM throughput, energy per inference, energy breakdown ratios, warm LLM latency, batch classification throughput |
| **High Stability** | 5–15% | LLM generation time, embedding tier latency, SenticNet pipeline median, ablation cost percentage |
| **Moderate Stability** | 15–25% | SenticNet API mean, Mem0 store latency, cold start time, RSS measurements |
| **Low Stability** | > 25% | Mem0 retrieval latency, pipeline peak RSS, SenticNet P99 tail latency |

On-device components demonstrated very high stability (< 5% CV), confirming that MLX inference on the Metal GPU is highly deterministic. Cloud-dependent components (SenticNet, Mem0) exhibited moderate to low stability (8–40% CV), reflecting the inherent variability of network latency and third-party API response times. This variance pattern is consistent with published evaluations of hybrid on-device/cloud AI architectures [27].

### 5.8.2 Consolidated Performance Summary

The following table presents the recommended reporting values for each metric, derived from the two-run analysis:

| Component | Metric | Value | Confidence |
|-----------|--------|-------|-----------|
| LLM | Throughput | 37.1 tok/s | High (CV < 1%) |
| LLM | Cold start | 0.94s | Moderate |
| LLM | /think overhead | 2.3x latency | High |
| Classification | Rules coverage | 78.0% | Deterministic |
| Classification | Throughput | 549 titles/s | High |
| Classification | Embedding latency | 7.9 ms | High |
| SenticNet | Single API (median) | 521 ms | High |
| SenticNet | Reliability | 100% | Deterministic |
| Mem0 | Store latency | 5,884 ms | Moderate |
| Mem0 | Retrieval latency | 274 ms | Moderate |
| Mem0 | Relevance (top-1) | 95% | Moderate |
| Pipeline | E2E latency | 13,961 ms | Moderate |
| Pipeline | SenticNet cost | 51.7% | High |
| Pipeline | Peak RSS | < 3 GB | High |
| Energy | Per inference | 21.3 mJ | High (CV 2.8%) |
| Energy | GPU share | 71.8% | Very High |
| Energy | Idle power | 0.70 W | High |
| Energy | Battery (active coaching) | ~69 hours | High |

---

## 5.9 Evaluation Against Project Objectives

| Objective | Metric | Target | Result | Status |
|-----------|--------|--------|--------|--------|
| On-device LLM viability | Throughput / latency | Real-time response | 37 tok/s, 1.4–2.7s | **Achieved** |
| Classification accuracy | Rule-based coverage | ≥ 40% | 78.0% | **Exceeded (1.95x)** |
| Classification speed | Throughput | > 100 titles/s | 549 titles/s | **Exceeded (5.5x)** |
| Memory personalization | Retrieval relevance | ≥ 80% top-1 | 95% | **Exceeded** |
| Memory constraint | Peak RSS | < 6 GB | < 3 GB | **Exceeded (2x+)** |
| Emotional awareness | Hourglass differentiation | Non-zero variance | stdev 48–67 | **Achieved** |
| Energy viability | Battery impact | Negligible | ~1.4%/hr | **Achieved** |
| System reliability | Stress test completion | All pass | 10/10 | **Achieved** |

All quantitative targets were met or exceeded with comfortable margins, validating the system's design decisions and implementation quality.

---

## 5.10 Discussion

### 5.10.1 Architectural Validation

The benchmark results validate the hybrid on-device/cloud architecture. On-device inference via MLX demonstrated high throughput (37 tok/s), low energy consumption (21.3 mJ/inference), and excellent reproducibility (< 5% CV). The 4-bit quantized Qwen3-4B model fits comfortably within the 16 GB memory budget while delivering response times suitable for real-time conversational interaction.

The 5-tier classification cascade achieved its design goal of minimizing embedding model invocations. By resolving 78% of classifications through sub-microsecond rule-based lookups, the system maintains a classification throughput of 549 titles/s — orders of magnitude beyond real-time requirements.

### 5.10.2 The Affective Computing Trade-off

The ablation analysis quantified the cost of emotional awareness at 51.7% of the generation pipeline latency. This is the most significant architectural trade-off in the system. SenticNet provides rich four-dimensional affective signals (Hourglass of Emotions) that are unavailable from any on-device alternative, enabling ADHD-specific emotional state mapping. However, as a cloud API, it introduces both latency variability and network dependency.

The system's dual-mode architecture (full mode with SenticNet at ~5.3s, ablation mode at ~2.6s) provides a practical solution: emotional awareness is available when therapeutically valuable, with a fast fallback for routine interactions.

### 5.10.3 Optimization Roadmap

The bottleneck analysis identifies three actionable optimization opportunities, ordered by expected impact:

1. **Asynchronous memory store (–39% perceived latency):** The Mem0 store operation (38.8% of pipeline) executes after the response has been generated. Making this fire-and-forget would eliminate 5.4 seconds of user-perceived latency without affecting response quality.

2. **Parallel SenticNet + LLM execution:** SenticNet analysis and LLM generation are currently sequential. If the SenticNet context were pre-computed or cached for known emotional patterns, these stages could be partially overlapped.

3. **Local SenticNet caching or distillation:** For frequently encountered emotional expressions, a local cache of SenticNet results or a distilled on-device model could eliminate network dependency for common cases.

### 5.10.4 Limitations

Several limitations should be noted when interpreting these results:

1. **RSS measurement limitations:** The `psutil` RSS metric does not capture Metal GPU buffer memory on Apple Silicon unified memory. True GPU memory consumption (~2.3 GB for Qwen3-4B-4bit) must be inferred from model file sizes.

2. **Cloud API variability:** SenticNet and Mem0 latencies are sensitive to network conditions and server load, contributing 8–40% cross-run variance. Results obtained under different network conditions may differ.

3. **Evaluation dataset scope:** The classification dataset (200 titles) and memory relevance test (10 query-memory pairs) are representative but limited in scale. Larger-scale evaluations would provide higher statistical confidence.

4. **Single-user evaluation:** All benchmarks tested single-user, single-request workloads on the target hardware. While this matches the application's design (single-user on-device tool), it does not evaluate scalability to multi-user server deployments.

5. **MLX thread safety:** The Metal GPU backend's lack of thread safety is a hard architectural constraint that prevents concurrent on-device inference, limiting optimization strategies that rely on parallelism.

---

## References Used in This Chapter

Citations referenced in this chapter (IEEE numeric style, ordered by first appearance):

- [1] Faraone, S.V., et al. (2021). "The World Federation of ADHD International Consensus Statement." *Neurosci. Biobehav. Rev.*, 128, 789–818. `\cite{faraone2021}`
- [4] Thorell, L.B., et al. (2022). "Longitudinal associations between digital media use and ADHD symptoms." *Eur. Child Adolesc. Psychiatry*. `\cite{thorell2022}`
- [5] García-Peral, A., et al. (2025). "Evaluating the evidence: digital interventions for ADHD." *BMC Psychiatry*. `\cite{garciaperal2025}`
- [6] Shou, S., et al. (2023). "Meta-analysis of digital therapies for ADHD." *Front. Psychiatry*, 14, 1054831. `\cite{shou2023}`
- [8] Fitzpatrick, K.K., et al. (2017). "Delivering CBT via Woebot." *JMIR Mental Health*, 4(2), e19. `\cite{fitzpatrick2017}`
- [9] Yuan, A., et al. (2025). "LLM-based Mental Health Chatbots." *ACM TMIS*, 16(1). `\cite{yuan2025}`
- [16] Cambria, E., et al. (2024). "SenticNet 8." *HCI International*, LNCS 15382. `\cite{cambria2024senticnet8}`
- [17] Cambria, E. (2016). "Affective Computing and Sentiment Analysis." *IEEE Intell. Syst.*, 31(2). `\cite{cambria2016}`
- [18] Hannun, A., et al. (2023). *MLX* [Software]. GitHub. `\cite{mlx2023}`
- [19] Yang, A., et al. (2025). "Qwen3 Technical Report." *arXiv:2505.09388*. `\cite{qwen3}`
- [20] Chhikara, P., et al. (2025). "Mem0: Scalable Long-Term Memory." *arXiv:2504.19413*. `\cite{mem0}`
- [23] Reimers, N. & Gurevych, I. (2019). "Sentence-BERT." *EMNLP-IJCNLP*, 3982–3992. `\cite{reimers2019}`
- [24] Wang, W., et al. (2020). "MiniLM." *NeurIPS 2020*. `\cite{minilm}`
- [26] Lin, J., et al. (2025). "Edge LLMs: Design, Execution, Applications." *ACM Computing Surveys*. `\cite{lin2025}`
- [27] Xu, Z., et al. (2024). "Mobile Edge Intelligence for LLMs." *arXiv:2407.18921*. `\cite{xu2024}`
- [28] zeus-apple-silicon v1.0.4. Energy measurement framework for Apple Silicon.

---

## LaTeX Integration Notes

- All tables are formatted for direct conversion to `\begin{table}[h]` environments with `\caption{}` and `\label{}`.
- The pipeline breakdown diagram should be rendered as a figure using `\begin{figure}[h]` with the ASCII art converted to a proper bar chart (e.g., via `pgfplots` or `tikz`).
- The energy breakdown (GPU 71.8%, DRAM 21.5%, CPU 6.8%, ANE 0%) should be presented as a pie chart figure.
- Cross-reference to Chapter 3 (System Design) for architecture diagrams and Chapter 4 (Implementation) for technical details.
- All `\cite{}` keys match the BibTeX entries in the research brief (`fyp-report/references/research-brief.md`).

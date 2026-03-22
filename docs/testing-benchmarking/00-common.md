# ADHD Second Brain — Evaluation & Benchmarking: Common Reference

## Read This First

This is the shared reference for a 6-phase evaluation pipeline. Each phase has its own instruction file (`01-phase1.md` through `06-phase6.md`). Execute them **in order** — each depends on the previous.

**Repository:** `https://github.com/avdheshcharjan/adhd-sentic-fyp`

---

## Files to Read Before Any Phase

Read these in order before starting work:

1. `models.md` — authoritative reference for all AI model decisions (overrides `blueprint.md`)
2. `docs/plans/2026-03-11-phase7-on-device-llm.md` — the 10-task Phase 7 plan
3. `sentic.txt` — SenticNet API details and Hourglass of Emotions model
4. `rui-mao-feedback-code-changes.md` — evaluation layer changes (Changes 1–6)
5. `services/` directory — check what services already exist and their interfaces

---

## Conventions

- Python 3.11+, async/await everywhere
- Pydantic v2 patterns (`model_validate_json`, `model_dump_json`)
- Test files go in `tests/`
- Evaluation/benchmark files go in `evaluation/`
- Use `pytest` + `pytest-asyncio` for all tests
- Target hardware: MacBook Pro M4 base, 16GB unified memory, macOS
- **Do not fabricate any numbers.** Every metric must come from actual measurement.
- Seed everything: `random.seed(42)`, `numpy.random.seed(42)` at the start of every eval script
- Time with `time.perf_counter()`, not `time.time()`
- Use `psutil` for memory measurement (reports RSS correctly on macOS)
- The existing code in `services/` and the ChatProcessor are the source of truth — adapt tests to match actual interfaces

---

## Dependencies

```bash
# Required
pip install pytest pytest-asyncio psutil loguru pingouin scipy --break-system-packages

# Optional (install if available)
pip install memory-profiler pytrec-eval-terrier zeus-apple-silicon --break-system-packages
```

---

## Target File Structure (After All Phases)

```
evaluation/
├── __init__.py
├── aggregate_results.py              # Phase 5
├── benchmarks/
│   ├── __init__.py
│   ├── runner.py                     # Phase 3
│   ├── bench_llm.py                  # Phase 3
│   ├── bench_classification.py       # Phase 3
│   ├── bench_senticnet.py            # Phase 3
│   ├── bench_memory.py               # Phase 3
│   ├── bench_pipeline.py             # Phase 3
│   └── bench_energy.py               # Phase 3
├── accuracy/
│   ├── __init__.py
│   ├── eval_classification.py        # Phase 4
│   ├── eval_coaching_quality.py      # Phase 4
│   ├── eval_senticnet.py             # Phase 4
│   └── eval_memory_retrieval.py      # Phase 4
├── data/
│   ├── window_titles_200.json        # Phase 2
│   ├── coaching_test_prompts.json    # Phase 2
│   ├── emotion_test_sentences.json   # Phase 2
│   ├── memory_test_profiles.json     # Phase 2
│   └── adhd_personas.json            # Phase 2
├── results/                          # Auto-populated
│   └── .gitkeep
└── persona_runner.py                 # From rui-mao-feedback (Change 3)

tests/
├── test_senticnet_service.py         # Phase 1
├── test_mlx_service.py               # Phase 1
├── test_embedding_service.py         # Phase 1
├── test_classification_cascade.py    # Phase 1
├── test_memory_service.py            # Phase 1
├── test_safety_pipeline.py           # Phase 1
└── test_full_pipeline.py             # Phase 1

services/
└── evaluation_logger.py              # Phase 5
```

---

## Phase Execution Order

| Phase | File | What It Does | Prerequisite |
|-------|------|--------------|--------------|
| 1 | `01-phase1-smoke-tests.md` | Verify every component works | Core Phase 7 pipeline complete |
| 2 | `02-phase2-test-data.md` | Create all test datasets | Phase 1 passes |
| 3 | `03-phase3-benchmarks.md` | System performance benchmarks | Phases 1 + 2 |
| 4 | `04-phase4-accuracy.md` | ML accuracy evaluations | Phases 1 + 2 |
| 5 | `05-phase5-logger-and-aggregator.md` | Evaluation logger + results aggregator | Phases 3 + 4 |
| 6 | `06-phase6-makefile.md` | One-command reproducibility | All above |

**Stop rule:** If Phase 1 smoke tests fail, fix failures before moving on. Benchmarks on broken components are meaningless.

---

## Pipeline Architecture Reference

The full chat pipeline flows like this:

```
User message
  → Safety input check (crisis keywords)
  → SenticNet analysis (Hourglass emotions) [skipped if ABLATION_MODE=True]
  → Mem0 memory retrieval (parallel with SenticNet)
  → Screen activity context fetch (parallel)
  → Prompt assembly (system prompt + emotion + memory + activity + user message)
  → Qwen3-4B inference via MLX (load-on-demand, ~2s cold start)
  → Safety output check
  → Mem0 memory store
  → Response delivery
```

Classification cascade (separate from chat, runs on screen monitor):

```
Window title
  → Tier 1: Rule-based regex/keyword matching (< 1ms)
  → Tier 2: Zero-shot embedding similarity via all-MiniLM-L6-v2 (< 50ms)
  → Tier 3: User correction cache lookup (< 1ms)
  → Result: productive / neutral / distracting
```

# Testing & Evaluation Strategy

> Unit tests, benchmarks, accuracy evaluations, and the FYP evaluation framework.
> **Version**: 1.0.0 | **Last Updated**: 2026-03-30

---

## Quick Reference

```bash
cd backend
make test           # Run all pytest smoke tests
make bench          # Run all benchmarks (requires tests to pass)
make eval           # Run all accuracy evaluations (requires tests to pass)
make all-eval       # Run everything + aggregate results
make summary        # Aggregate existing results (no re-run)
make clean-results  # Delete all results (keep data)
```

All commands use `python3.11` (hardcoded in Makefile).

---

## 1. Unit & Integration Tests

```
backend/tests/
├── test_activity_classifier.py        # 5-layer classification cascade
├── test_adhd_metrics.py               # Rolling metrics, state transitions
├── test_jitai_engine.py               # Intervention rules, cooldowns, gates
├── test_xai_explainer.py              # Explanation generation
├── test_senticnet_client.py           # HTTP client, sanitization, error handling
├── test_senticnet_pipeline.py         # Tier routing, safety thresholds
├── test_senticnet_pipeline_safety.py  # Safety-specific edge cases
├── test_chat_processor.py             # Full chat pipeline (SenticNet → LLM → Memory)
├── test_memory_service.py             # Mem0 integration
├── test_whoop_service.py              # Whoop CLI wrapper
├── test_insights_service.py           # Dashboard aggregations
├── test_full_pipeline.py              # End-to-end integration
├── test_setfit_wiring.py              # SetFit integration into screen pipeline
├── test_screen_endpoint.py            # Screen API contract
├── test_focus_service.py              # Task creation, focus timer
├── test_focus_relevance.py            # Off-task embedding similarity
├── test_vent_service.py               # 4-layer safety vent pipeline
├── test_brain_dump_service.py         # Brain dump capture + AI summary
├── test_snapshot_service.py           # Daily snapshot save/retrieve
├── test_evaluation_logger.py          # JSONL logging for ablation
├── test_evaluation_endpoints.py       # Ablation toggle API
├── test_questionnaires.py             # ASRS-v1.1 and SUS scoring
├── test_action_suggestions.py         # Suggested actions from SenticNet
├── test_google_calendar.py            # Google OAuth + event fetching
└── conftest.py                        # Shared fixtures
```

Run:
```bash
make test                              # All tests with 300s timeout
python3.11 -m pytest tests/test_jitai_engine.py -v    # Single module
python3.11 -m pytest tests/ --cov=services --cov-report=html  # With coverage
python3.11 -m pytest tests/ -v -m "not slow"           # Skip slow SenticNet tests
```

---

## 2. Performance Benchmarks

```
evaluation/benchmarks/
├── runner.py                   # Orchestrator (--all | --component NAME)
├── bench_classification.py     # Activity classification cascade latency
├── bench_llm.py                # MLX Qwen3-4B inference speed (tok/s)
├── bench_memory.py             # Mem0 memory retrieval latency
├── bench_pipeline.py           # Full pipeline throughput (screen → response)
├── bench_senticnet.py          # SenticNet 13-API round-trip latency
└── bench_energy.py             # Energy/power usage on Apple Silicon
```

Run:
```bash
make bench              # All benchmarks (depends on tests passing)
make bench-llm          # LLM benchmarks only
make bench-classify     # Classification only
make bench-pipeline     # Full pipeline only
```

### Key Results

| Component | Metric | Value |
|-----------|--------|-------|
| Activity Classification | P95 latency | <25ms |
| SetFit Emotion | P95 latency | <50ms |
| SenticNet Pipeline (13 APIs) | Mean latency | ~3.7s |
| MLX LLM (Qwen3-4B) | Tokens/sec (M4) | ~37 tok/s |
| Memory Retrieval (Mem0) | Hit@1 accuracy | 89% |
| Memory Retrieval (Mem0) | Hit@3 accuracy | 97% |
| Full Pipeline (screen) | P95 latency | <100ms |

---

## 3. Accuracy Evaluations

```
evaluation/accuracy/
├── eval_classification.py             # Activity classification accuracy
├── eval_coaching_quality.py           # LLM coaching quality (win rate vs baseline)
├── eval_senticnet.py                  # SenticNet emotion recognition accuracy
├── eval_memory_retrieval.py           # Memory retrieval Hit@K
├── train_and_eval_setfit.py           # Approach B: SetFit training + evaluation
├── train_and_eval_hybrid.py           # Approach A: Hybrid training + evaluation
├── train_and_eval_finetune.py         # Approach C: DistilBERT training + evaluation
├── train_and_eval_finetune_augmented.py  # Approach C with 30K augmented data
└── train_and_eval_kaggle.py           # Kaggle dataset training
```

Run:
```bash
make eval               # All accuracy evaluations
make eval-classify      # Classification only
make eval-coaching      # Coaching quality only
make eval-senticnet     # SenticNet only
make eval-memory        # Memory retrieval only
```

---

## 4. Emotion Classifier Approaches

Three parallel approaches evaluated for mapping screen activity to 6 ADHD emotional states:

| Approach | Architecture | Accuracy | Training Data | Status |
|----------|-------------|----------|---------------|--------|
| A: Hybrid | Sentence embeddings + SenticNet features → sklearn | 74% (emb-only) | 210 sentences | Experimental |
| B: SetFit | Contrastive fine-tuned all-mpnet-base-v2 → LogReg | **86%** | 210 sentences, 1 epoch | **Production** |
| C: DistilBERT | Full fine-tune DistilBERT | 62-72% | 210-30K sentences | Experimental |

**Labels**: `joyful` · `focused` · `frustrated` · `anxious` · `disengaged` · `overwhelmed`

**Key findings**:
- SetFit (B) achieves 86% with just 210 sentences and 1 epoch of contrastive training
- CoSENT loss + all-unique-pair mining + hard negatives drove accuracy from 80% → 86%
- 2 epochs overfit (84% vs 86%) — 1 epoch is optimal
- Adding 288 LLM-generated boundary sentences REGRESSED accuracy to 82% — class imbalance collapsed anxious class
- DistilBERT (C) needs 30K+ samples to approach SetFit accuracy but never surpasses it
- SenticNet features HURT hybrid classifier (70% with SN vs 74% embedding-only)

---

## 5. Ablation Testing

Runtime A/B comparison of system with/without SenticNet affective computing.

| Endpoint | Purpose |
|----------|---------|
| `POST /eval/ablation` | Toggle SenticNet ON/OFF at runtime |
| `GET /eval/ablation` | Get current ablation status |
| `POST /eval/logging` | Toggle structured JSONL interaction logging |

### EvaluationLogEntry (36 fields)

Each chat interaction is logged with:
- **Identity**: interaction_id, session_id, timestamp
- **Input**: user_message, conversation_id, message_length
- **SenticNet**: senticnet_available, primary_emotion, polarity_score, intensity_score, safety_level, hourglass dimensions, engagement_score, wellbeing_score
- **LLM**: model_used, thinking_mode, response_text, response_length, latency_ms, token_count
- **Memory**: memory_context_used, memory_items_retrieved
- **Ablation**: ablation_mode (true = SenticNet bypassed)

Logs stored in `backend/data/evaluation_logs/*.jsonl`.

---

## 6. LLM Persona Simulation

5 diverse ADHD personas driven by external LLMs against the coaching system:

```bash
python3.11 -m evaluation.persona_runner --all --provider openai
python3.11 -m evaluation.persona_runner --persona anxious_student --provider gemini
python3.11 -m evaluation.analyze_results
```

Personas vary by: ADHD subtype, severity, age, gender, occupation. Providers: OpenAI GPT-4o, Google Gemini, Qwen.

Post-hoc analysis:
- Hourglass-to-ADHD correlation across persona conversations
- Ablation comparison (SenticNet ON vs OFF)
- Response quality metrics

---

## 7. Standardized Questionnaires

```python
# evaluation/questionnaires.py
from evaluation.questionnaires import score_asrs, score_sus

# ASRS-v1.1 (ADHD screening)
result = score_asrs([3, 4, 2, 3, 4, 3])  # 6 items, 0-4 scale
# → {total: 19, severity_band: "high_positive", inattention: 9, hyperactivity: 10}

# SUS (System Usability Scale)
result = score_sus([4, 2, 5, 1, 4, 2, 5, 1, 4, 2])  # 10 items, 1-5 scale
# → {score: 77.5, percentile_rank: "good", acceptability: "acceptable"}
```

---

## 8. Evaluation Data

```
evaluation/data/
├── emotion_training_data.json          # 498 sentences (210 original + 288 generated)
├── emotion_test_sentences.json         # 50 hand-labeled test sentences
├── augmented_emotion_training_data.json # 30K balanced (4.3MB)
├── generated_sentences.json            # 288 LLM-generated boundary sentences
├── adhd_personas.json                  # 5 ADHD persona definitions
├── coaching_test_prompts.json          # Test prompts for coaching quality eval
├── memory_test_profiles.json           # Test profiles for memory retrieval eval
├── window_titles_200.json              # 200 real window titles for classification eval
├── kaggle_combined_training_data.json  # Combined Kaggle mental health data (11.9MB)
├── collect_emotion_datasets.py         # Data collection script
├── generate_boundary_sentences.py      # LLM boundary sentence generator
└── process_kaggle_datasets.py          # Kaggle dataset processor
```

---

## 9. Results Aggregation

```bash
make summary    # Aggregate all results
```

Scans `evaluation/results/` for timestamped JSON files and produces:
- Summary JSON (`summary_YYYYMMDD_HHMMSS.json`)
- Summary Markdown (`summary_YYYYMMDD_HHMMSS.md`)
- Console output with key metrics

Results directory contains 63+ timestamped JSON files across:
- `approach_a_hybrid_*.json`, `approach_b_setfit_*.json`, `approach_c_finetune_*.json`
- `benchmark_classification_*.json`, `benchmark_llm_*.json`, `benchmark_pipeline_*.json`
- `benchmark_memory_*.json`, `benchmark_senticnet_*.json`, `benchmark_energy_*.json`
- `classification_accuracy_*.json`, `coaching_quality_*.json`
- `comparison_report.json`

---

## 10. Makefile Reference

| Target | Depends On | Command |
|--------|-----------|---------|
| `test` | — | `pytest tests/ -v --timeout=300` |
| `bench` | `test` | `evaluation.benchmarks.runner --all` |
| `bench-llm` | — | `evaluation.benchmarks.runner --component llm` |
| `bench-classify` | — | `evaluation.benchmarks.runner --component classification` |
| `bench-pipeline` | — | `evaluation.benchmarks.runner --component pipeline` |
| `eval` | `test` | 4 accuracy scripts sequentially |
| `eval-classify` | — | `evaluation.accuracy.eval_classification` |
| `eval-coaching` | — | `evaluation.accuracy.eval_coaching_quality` |
| `eval-senticnet` | — | `evaluation.accuracy.eval_senticnet` |
| `eval-memory` | — | `evaluation.accuracy.eval_memory_retrieval` |
| `summary` | — | `evaluation.aggregate_results` |
| `all-eval` | `bench`, `eval` | `evaluation.aggregate_results` |
| `clean-results` | — | Delete all result JSONs (preserves data/) |

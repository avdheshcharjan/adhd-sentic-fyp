# ADHD Second Brain — Evaluation Suite

## Quick Start

```bash
# Install dependencies
pip install pytest pytest-asyncio psutil loguru pingouin scipy --break-system-packages

# Run everything
make all-eval
```

## What Gets Measured

### System Performance (Phase 3)
- LLM inference: cold start, TTFT, tokens/sec, peak memory
- Classification cascade: per-tier latency, tier coverage, batch throughput
- SenticNet: API latency, reliability, dimension distribution
- Mem0: store/retrieve latency, scaling behavior
- Full pipeline: end-to-end waterfall, warm vs cold, ablation timing

### ML Accuracy (Phase 4)
- Window title classification: macro-F1, per-class P/R/F1, confusion matrix
- Coaching quality: 6-dimension scoring via LLM-as-judge, ablation win/tie/loss
- Emotion detection: emotion category F1, Hourglass dimension correlations
- Memory retrieval: Hit@1, Hit@3, nDCG@3

### Results
All results are saved as JSON in `evaluation/results/`.
Run `make summary` to aggregate into a formatted report.

## Test Data
All test datasets are in `evaluation/data/`. See Phase 2 instructions for format details.

## Reproducibility
- All scripts use seed 42
- System info is recorded in every result file
- `make all-eval` reproduces everything from scratch

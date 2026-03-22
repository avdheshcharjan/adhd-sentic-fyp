# Phase 6: Makefile & Reproducibility

## Context

Read `00-common.md` first. All previous phases must be complete.

**Goal:** Create a Makefile that lets anyone reproduce all evaluation results with a single command. Also verify everything works end-to-end.

---

## Task 6.1: Create the Makefile

**File:** `Makefile` (project root — append to existing if one exists, otherwise create)

```makefile
# ============================================================
# ADHD Second Brain — Evaluation & Benchmarking
# ============================================================
# Usage:
#   make test          — Run all smoke tests
#   make bench         — Run all benchmarks (requires tests to pass)
#   make eval          — Run all accuracy evaluations (requires tests to pass)
#   make all-eval      — Run everything and aggregate results
#   make bench-llm     — Quick: LLM benchmarks only
#   make eval-classify — Quick: classification accuracy only
#   make summary       — Aggregate existing results (no re-run)
#   make clean-results — Delete all results (keep data)
# ============================================================

.PHONY: test bench eval all-eval bench-llm eval-classify summary clean-results

# ---- Phase 1: Smoke tests ----
test:
	pytest tests/ -v --timeout=300

# ---- Phase 3: Benchmarks (depends on tests passing) ----
bench: test
	python -m evaluation.benchmarks.runner --all

bench-llm:
	python -m evaluation.benchmarks.runner --component llm

bench-classify:
	python -m evaluation.benchmarks.runner --component classification

bench-pipeline:
	python -m evaluation.benchmarks.runner --component pipeline

# ---- Phase 4: Accuracy evaluations ----
eval: test
	python -m evaluation.accuracy.eval_classification
	python -m evaluation.accuracy.eval_coaching_quality
	python -m evaluation.accuracy.eval_senticnet
	python -m evaluation.accuracy.eval_memory_retrieval

eval-classify:
	python -m evaluation.accuracy.eval_classification

eval-coaching:
	python -m evaluation.accuracy.eval_coaching_quality

eval-senticnet:
	python -m evaluation.accuracy.eval_senticnet

eval-memory:
	python -m evaluation.accuracy.eval_memory_retrieval

# ---- Phase 5: Aggregation ----
summary:
	python -m evaluation.aggregate_results

# ---- Full pipeline ----
all-eval: bench eval
	python -m evaluation.aggregate_results

# ---- Cleanup ----
clean-results:
	rm -f evaluation/results/benchmark_*.json
	rm -f evaluation/results/*_accuracy_*.json
	rm -f evaluation/results/coaching_*.json
	rm -f evaluation/results/summary_*.json
	rm -f evaluation/results/summary_*.md
	@echo "Results cleaned. Test data preserved."
```

---

## Task 6.2: Add a Reproducibility Header to All Scripts

Every evaluation script should record its execution context. Add this utility:

**File:** `evaluation/utils.py`

```python
"""Shared utilities for evaluation scripts."""

import json
import os
import platform
import sys
import time
import random
import numpy as np
from datetime import datetime, timezone


def seed_everything(seed: int = 42):
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # Add torch seed here if torch is ever used


def get_system_info() -> dict:
    """Collect system information for reproducibility."""
    info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "python": sys.version,
        "chip": platform.processor() or platform.machine(),
        "ram_gb": round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3), 1)
            if hasattr(os, "sysconf") else "unknown",
    }
    try:
        import mlx
        info["mlx_version"] = mlx.__version__
    except ImportError:
        info["mlx_version"] = "not installed"
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except ImportError:
        pass
    return info


def save_result(data: dict, prefix: str, results_dir: str = "evaluation/results"):
    """Save evaluation result with timestamp."""
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.json"
    filepath = os.path.join(results_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Results saved to: {filepath}")
    return filepath


def compute_stats(values: list) -> dict:
    """Compute summary statistics for a list of numeric values."""
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "stdev": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "n": len(arr),
    }
```

Every evaluation script should call `seed_everything()` at the top and include `get_system_info()` in its output.

---

## Task 6.3: End-to-End Verification

Run the full pipeline and verify everything works:

```bash
# 1. Verify test data exists
python -c "
import json, os
for f in ['window_titles_200.json','coaching_test_prompts.json','emotion_test_sentences.json','memory_test_profiles.json','adhd_personas.json']:
    data = json.load(open(f'evaluation/data/{f}'))
    print(f'  {f}: {len(data)} items')
"

# 2. Run everything
make all-eval

# 3. Verify results
ls -la evaluation/results/
python -c "
import os, json
results = [f for f in os.listdir('evaluation/results') if f.endswith('.json')]
print(f'Total result files: {len(results)}')
for f in sorted(results):
    print(f'  {f}')
"

# 4. Check the markdown summary exists and has content
cat evaluation/results/summary_*.md | head -50
```

---

## Task 6.4: Create a README for the Evaluation Directory

**File:** `evaluation/README.md`

```markdown
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
```

---

## Completion Criteria

1. `make all-eval` runs end-to-end without errors
2. `evaluation/results/` contains JSON files for all benchmarks and accuracy evaluations
3. `evaluation/results/summary_*.md` exists with all metrics filled in
4. `evaluation/utils.py` provides shared seed/stats/save utilities
5. `evaluation/README.md` documents the evaluation suite
6. Every result JSON includes `system_info` with hardware/software versions

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

PYTHON := python3.11

.PHONY: test bench eval all-eval bench-llm bench-classify bench-pipeline eval-classify eval-coaching eval-senticnet eval-memory summary clean-results

# ---- Phase 1: Smoke tests ----
test:
	$(PYTHON) -m pytest tests/ -v --timeout=300

# ---- Phase 3: Benchmarks (depends on tests passing) ----
bench: test
	$(PYTHON) -m evaluation.benchmarks.runner --all

bench-llm:
	$(PYTHON) -m evaluation.benchmarks.runner --component llm

bench-classify:
	$(PYTHON) -m evaluation.benchmarks.runner --component classification

bench-pipeline:
	$(PYTHON) -m evaluation.benchmarks.runner --component pipeline

# ---- Phase 4: Accuracy evaluations ----
eval: test
	$(PYTHON) -m evaluation.accuracy.eval_classification
	$(PYTHON) -m evaluation.accuracy.eval_coaching_quality
	$(PYTHON) -m evaluation.accuracy.eval_senticnet
	$(PYTHON) -m evaluation.accuracy.eval_memory_retrieval

eval-classify:
	$(PYTHON) -m evaluation.accuracy.eval_classification

eval-coaching:
	$(PYTHON) -m evaluation.accuracy.eval_coaching_quality

eval-senticnet:
	$(PYTHON) -m evaluation.accuracy.eval_senticnet

eval-memory:
	$(PYTHON) -m evaluation.accuracy.eval_memory_retrieval

# ---- Phase 5: Aggregation ----
summary:
	$(PYTHON) -m evaluation.aggregate_results

# ---- Full pipeline ----
all-eval: bench eval
	$(PYTHON) -m evaluation.aggregate_results

# ---- Cleanup ----
clean-results:
	rm -f evaluation/results/benchmark_*.json
	rm -f evaluation/results/*_accuracy_*.json
	rm -f evaluation/results/coaching_*.json
	rm -f evaluation/results/summary_*.json
	rm -f evaluation/results/summary_*.md
	@echo "Results cleaned. Test data preserved."

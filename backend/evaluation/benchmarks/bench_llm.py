"""
LLM Inference Benchmark (Qwen3-4B via MLX)

Measures:
1. Cold start time (model load)
2. Time-to-first-token (TTFT) — approximated via generation time
3. Generation throughput (tokens/second)
4. Peak memory usage
5. Thinking mode comparison (/think vs /no_think)
"""

import gc
import random
import statistics
import time
from pathlib import Path

import numpy as np
import psutil

random.seed(42)
np.random.seed(42)

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

SYSTEM_PROMPT = (
    "You are a supportive ADHD coach. Give brief, actionable advice. "
    "Under 3 sentences."
)


def run_benchmark():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from evaluation.benchmarks.runner import save_result

    process = psutil.Process()
    metrics = {}
    raw_measurements = []

    # ── 1. Cold Start Time ────────────────────────────────────────
    print("\n[1/5] Cold Start Time (5 measurements)")

    cold_start_times = []
    for i in range(5):
        # Force unload
        gc.collect()

        from mlx_lm import load
        start = time.perf_counter()
        model, tokenizer = load(path_or_hf_repo="mlx-community/Qwen3-4B-4bit")
        elapsed = time.perf_counter() - start
        cold_start_times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s")

        # Unload
        del model, tokenizer
        gc.collect()

    metrics["cold_start"] = {
        "mean_s": round(statistics.mean(cold_start_times), 2),
        "median_s": round(statistics.median(cold_start_times), 2),
        "min_s": round(min(cold_start_times), 2),
        "max_s": round(max(cold_start_times), 2),
        "stdev_s": round(statistics.stdev(cold_start_times), 2) if len(cold_start_times) > 1 else 0,
    }
    raw_measurements.append({"test": "cold_start", "times_s": [round(t, 3) for t in cold_start_times]})

    # ── Load model once for remaining tests ────────────────────────
    print("\n  Loading model for remaining tests...")
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(path_or_hf_repo="mlx-community/Qwen3-4B-4bit")
    sampler = make_sampler(temp=0.7)

    def _generate(prompt_text: str, use_thinking: bool = False, max_tokens: int = 150) -> tuple[str, float, int]:
        """Generate and return (response, total_time_ms, approx_tokens)."""
        thinking_prefix = "/think\n" if use_thinking else "/no_think\n"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{thinking_prefix}{prompt_text}"},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        start = time.perf_counter()
        response = generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens, sampler=sampler)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Approximate token count (rough: 4 chars per token)
        approx_tokens = len(response) // 4
        return response, elapsed_ms, max(approx_tokens, 1)

    # ── 2. Generation Time per Prompt Length ────────────────────────
    print("\n[2/5] Generation Time (10 iterations per prompt length)")
    # Using 10 iterations instead of 30 to keep runtime reasonable

    generation_metrics = {}
    for label, prompt_text in PROMPTS.items():
        times = []
        token_counts = []

        for i in range(10):
            if i < 2:
                # Warmup — don't record
                _generate(prompt_text, use_thinking=False, max_tokens=100)
                continue
            response, elapsed_ms, tokens = _generate(prompt_text, use_thinking=False, max_tokens=150)
            times.append(elapsed_ms)
            token_counts.append(tokens)

        # Remove warmup entries (first 2 were skipped)
        sorted_times = sorted(times)
        generation_metrics[label] = {
            "mean_ms": round(statistics.mean(times), 1),
            "median_ms": round(statistics.median(times), 1),
            "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)], 1),
            "min_ms": round(min(times), 1),
            "max_ms": round(max(times), 1),
            "mean_tokens": round(statistics.mean(token_counts), 0),
        }
        print(f"  {label:8s}: mean={generation_metrics[label]['mean_ms']:.0f}ms  "
              f"median={generation_metrics[label]['median_ms']:.0f}ms  "
              f"tokens≈{generation_metrics[label]['mean_tokens']:.0f}")

    metrics["generation_time"] = generation_metrics
    raw_measurements.append({"test": "generation_time", "data": generation_metrics})

    # ── 3. Throughput (tokens/second) ──────────────────────────────
    print("\n[3/5] Generation Throughput (tokens/second)")

    throughput_metrics = {}
    for label, prompt_text in PROMPTS.items():
        tok_per_sec_list = []
        for _ in range(8):
            response, elapsed_ms, tokens = _generate(prompt_text, use_thinking=False, max_tokens=150)
            if elapsed_ms > 0:
                tok_per_sec = tokens / (elapsed_ms / 1000)
                tok_per_sec_list.append(tok_per_sec)

        throughput_metrics[label] = {
            "mean_tok_s": round(statistics.mean(tok_per_sec_list), 1),
            "median_tok_s": round(statistics.median(tok_per_sec_list), 1),
            "min_tok_s": round(min(tok_per_sec_list), 1),
            "max_tok_s": round(max(tok_per_sec_list), 1),
        }
        print(f"  {label:8s}: mean={throughput_metrics[label]['mean_tok_s']:.1f} tok/s  "
              f"median={throughput_metrics[label]['median_tok_s']:.1f} tok/s")

    metrics["throughput"] = throughput_metrics
    raw_measurements.append({"test": "throughput", "data": throughput_metrics})

    # ── 4. Memory Usage ───────────────────────────────────────────
    print("\n[4/5] Memory Usage")

    rss_during = process.memory_info().rss / (1024 * 1024)
    print(f"  RSS with model loaded: {rss_during:.0f} MB")

    # Generate to see peak
    _generate(PROMPTS["long"], use_thinking=False, max_tokens=200)
    rss_peak = process.memory_info().rss / (1024 * 1024)
    print(f"  RSS after generation:  {rss_peak:.0f} MB")

    # Unload
    del model, tokenizer
    gc.collect()
    time.sleep(1)
    rss_after_unload = process.memory_info().rss / (1024 * 1024)
    print(f"  RSS after unload:      {rss_after_unload:.0f} MB")

    metrics["memory"] = {
        "rss_with_model_mb": round(rss_during, 0),
        "rss_peak_generation_mb": round(rss_peak, 0),
        "rss_after_unload_mb": round(rss_after_unload, 0),
        "model_footprint_mb": round(rss_during - rss_after_unload, 0),
    }
    raw_measurements.append({"test": "memory", "data": metrics["memory"]})

    # ── 5. Thinking Mode Comparison ───────────────────────────────
    print("\n[5/5] Thinking Mode Comparison (medium prompt, 5 iterations each)")

    # Reload model
    model, tokenizer = load(path_or_hf_repo="mlx-community/Qwen3-4B-4bit")

    think_times = []
    no_think_times = []
    think_tokens = []
    no_think_tokens = []

    for _ in range(5):
        _, elapsed_ms, tokens = _generate(PROMPTS["medium"], use_thinking=True, max_tokens=200)
        think_times.append(elapsed_ms)
        think_tokens.append(tokens)

    for _ in range(5):
        _, elapsed_ms, tokens = _generate(PROMPTS["medium"], use_thinking=False, max_tokens=200)
        no_think_times.append(elapsed_ms)
        no_think_tokens.append(tokens)

    metrics["thinking_mode"] = {
        "think": {
            "mean_ms": round(statistics.mean(think_times), 0),
            "median_ms": round(statistics.median(think_times), 0),
            "mean_tokens": round(statistics.mean(think_tokens), 0),
        },
        "no_think": {
            "mean_ms": round(statistics.mean(no_think_times), 0),
            "median_ms": round(statistics.median(no_think_times), 0),
            "mean_tokens": round(statistics.mean(no_think_tokens), 0),
        },
    }
    print(f"  /think:    mean={metrics['thinking_mode']['think']['mean_ms']:.0f}ms  "
          f"tokens≈{metrics['thinking_mode']['think']['mean_tokens']}")
    print(f"  /no_think: mean={metrics['thinking_mode']['no_think']['mean_ms']:.0f}ms  "
          f"tokens≈{metrics['thinking_mode']['no_think']['mean_tokens']}")

    raw_measurements.append({"test": "thinking_mode", "data": metrics["thinking_mode"]})

    # Cleanup
    del model, tokenizer
    gc.collect()

    # ── Save Results ──────────────────────────────────────────────
    save_result("llm", metrics, raw_measurements)
    print("\n✓ LLM benchmark complete")


if __name__ == "__main__":
    run_benchmark()

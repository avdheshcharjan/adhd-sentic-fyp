"""
SenticNet API Benchmark

Measures:
1. Single API call latency (emotion endpoint)
2. Full pipeline analysis latency by input length
3. API reliability (success/failure rate)
4. Hourglass dimension distribution from emotion test sentences
"""

import asyncio
import json
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"

# Test sentences for single lookups
SINGLE_LOOKUP_SENTENCES = [
    "I feel happy today",
    "This is frustrating",
    "I am overwhelmed",
    "Great progress",
    "I can't focus",
    "Everything is fine",
    "I hate this",
    "Wonderful news",
    "I'm scared",
    "Boring task",
]

# Varying-length inputs
SHORT_10W = "I feel really frustrated and overwhelmed by my workload today."
MEDIUM_50W = (
    "I've been trying to work on my report for the past hour but I keep "
    "checking social media. I feel guilty about it but can't seem to stop. "
    "Every time I try to concentrate, my mind wanders to something else. "
    "I know I should be more disciplined but it feels impossible right now."
)
LONG_100W = (
    "I'm a university student with ADHD. Today I need to finish a 3000-word "
    "essay that's due tomorrow, attend two online lectures, reply to emails "
    "from my supervisor, and prepare for a group presentation on Friday. I'm "
    "feeling completely overwhelmed and don't know where to start. I've already "
    "wasted most of the morning scrolling on my phone. My medication is making "
    "me feel jittery but not actually helping me focus. Can you help me figure "
    "out what to do first? I feel like everyone else has it together except me "
    "and that makes everything worse."
)
VERY_LONG_200W = (
    "I've been struggling with ADHD my entire life. Recently diagnosed at 28 "
    "after years of thinking I was just lazy or unmotivated. The medication helps "
    "on some days but on others it makes me feel like a zombie. My work performance "
    "has been declining because I can't maintain focus during long meetings and I "
    "miss details in emails that my colleagues catch immediately. My manager has "
    "been understanding but I can see their patience wearing thin. Last week I "
    "forgot about an important client presentation and had to wing it, which went "
    "terribly. I've tried using productivity apps, timers, to-do lists, bullet "
    "journals, and nothing sticks for more than two weeks. My relationship is "
    "suffering too because my partner feels like I never listen to them, but I'm "
    "genuinely trying my hardest. I feel like I'm failing at every aspect of my "
    "life simultaneously. The worst part is knowing that I'm intelligent enough "
    "to succeed but something in my brain just won't cooperate. I've read that "
    "emotional dysregulation is common with ADHD and that resonates deeply. Small "
    "setbacks feel catastrophic and positive moments feel fragile. I need strategies "
    "that actually work for someone like me, not generic productivity advice. Please help."
)


async def _run_async():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from services.senticnet_client import SenticNetClient
    from services.senticnet_pipeline import SenticNetPipeline
    from evaluation.benchmarks.runner import save_result

    client = SenticNetClient()
    pipeline = SenticNetPipeline()

    metrics = {}
    raw_measurements = []

    # ── 1. Single API Call Latency ─────────────────────────────────
    print("\n[1/4] Single Emotion API Latency (50 calls)")

    single_latencies = []
    single_results = []
    successes = 0
    failures = 0

    for i in range(50):
        sentence = SINGLE_LOOKUP_SENTENCES[i % len(SINGLE_LOOKUP_SENTENCES)]
        start = time.perf_counter()
        try:
            result = await client.get_emotion(sentence)
            elapsed_ms = (time.perf_counter() - start) * 1000
            single_latencies.append(elapsed_ms)
            if result is not None:
                successes += 1
                single_results.append({"sentence": sentence, "result": result, "latency_ms": round(elapsed_ms, 2)})
            else:
                failures += 1
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            single_latencies.append(elapsed_ms)
            failures += 1
            single_results.append({"sentence": sentence, "error": str(e), "latency_ms": round(elapsed_ms, 2)})

    sorted_latencies = sorted(single_latencies)
    metrics["single_lookup_latency"] = {
        "mean_ms": round(statistics.mean(single_latencies), 1),
        "median_ms": round(statistics.median(single_latencies), 1),
        "p95_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.95)], 1),
        "p99_ms": round(sorted_latencies[int(len(sorted_latencies) * 0.99)], 1),
        "min_ms": round(min(single_latencies), 1),
        "max_ms": round(max(single_latencies), 1),
        "success_count": successes,
        "failure_count": failures,
    }
    print(f"  Mean: {metrics['single_lookup_latency']['mean_ms']}ms")
    print(f"  Median: {metrics['single_lookup_latency']['median_ms']}ms")
    print(f"  P95: {metrics['single_lookup_latency']['p95_ms']}ms")
    print(f"  P99: {metrics['single_lookup_latency']['p99_ms']}ms")
    print(f"  Success: {successes}/{successes + failures}")

    raw_measurements.append({"test": "single_lookup", "results": single_results})

    # ── 2. Full Pipeline Analysis by Input Length ──────────────────
    print("\n[2/4] Full Pipeline Latency by Input Length (5 iterations each)")

    length_tests = {
        "10_words": SHORT_10W,
        "50_words": MEDIUM_50W,
        "100_words": LONG_100W,
        "200_words": VERY_LONG_200W,
    }

    length_metrics = {}
    for label, text in length_tests.items():
        word_count = len(text.split())
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            try:
                result = await pipeline.analyze(text, mode="full")
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)
                print(f"    Error on {label}: {e}")

        length_metrics[label] = {
            "word_count": word_count,
            "mean_ms": round(statistics.mean(latencies), 1),
            "median_ms": round(statistics.median(latencies), 1),
            "min_ms": round(min(latencies), 1),
            "max_ms": round(max(latencies), 1),
        }
        print(f"  {label} ({word_count}w): mean={length_metrics[label]['mean_ms']}ms  "
              f"median={length_metrics[label]['median_ms']}ms")

    metrics["pipeline_latency_by_length"] = length_metrics
    raw_measurements.append({"test": "pipeline_by_length", "data": length_metrics})

    # ── 3. API Reliability (100 requests) ─────────────────────────
    print("\n[3/4] API Reliability (100 requests across multiple endpoints)")

    reliability_results = {"success": 0, "failure": 0, "failure_types": {}}
    test_text = "I feel overwhelmed with my work today"

    endpoints = ["polarity", "intensity", "emotion", "depression", "toxicity", "engagement", "wellbeing"]
    calls_made = 0

    for i in range(100):
        endpoint = endpoints[i % len(endpoints)]
        try:
            method = getattr(client, f"get_{endpoint}")
            result = await method(test_text)
            if result is not None:
                reliability_results["success"] += 1
            else:
                reliability_results["failure"] += 1
                reliability_results["failure_types"]["null_response"] = \
                    reliability_results["failure_types"].get("null_response", 0) + 1
            calls_made += 1
        except Exception as e:
            reliability_results["failure"] += 1
            error_type = type(e).__name__
            reliability_results["failure_types"][error_type] = \
                reliability_results["failure_types"].get(error_type, 0) + 1
            calls_made += 1

    total = reliability_results["success"] + reliability_results["failure"]
    success_rate = reliability_results["success"] / total * 100 if total > 0 else 0
    print(f"  Total calls: {total}")
    print(f"  Successes: {reliability_results['success']}")
    print(f"  Failures: {reliability_results['failure']}")
    print(f"  Success rate: {success_rate:.1f}%")
    if reliability_results["failure_types"]:
        print(f"  Failure types: {reliability_results['failure_types']}")

    metrics["api_reliability"] = {
        "total_calls": total,
        "success": reliability_results["success"],
        "failure": reliability_results["failure"],
        "success_rate_pct": round(success_rate, 1),
        "failure_types": reliability_results["failure_types"],
    }
    raw_measurements.append({"test": "reliability", "data": metrics["api_reliability"]})

    # ── 4. Hourglass Dimension Distribution ────────────────────────
    # NOTE: Hourglass values (introspection, temper, attitude, sensitivity)
    # are ONLY available via the ensemble API endpoint, not the individual
    # emotion endpoint. The pipeline's _tier2_emotion() doesn't populate
    # these fields. We call the ensemble API directly here.
    print("\n[4/4] Hourglass Dimension Distribution (50 emotion sentences via ensemble)")

    with open(DATA_DIR / "emotion_test_sentences.json") as f:
        emotion_sentences = json.load(f)

    hourglass_data = {"introspection": [], "temper": [], "attitude": [], "sensitivity": []}
    analyzed_count = 0
    skipped_count = 0

    for item in emotion_sentences[:50]:
        try:
            ensemble = await client.get_ensemble(item["sentence"])
            if ensemble:
                # Ensemble returns hourglass as string values, parse to float
                for dim in ["introspection", "temper", "attitude", "sensitivity"]:
                    raw_val = ensemble.get(dim, "0")
                    try:
                        val = float(str(raw_val).strip().rstrip("%"))
                        hourglass_data[dim].append(val)
                    except (ValueError, TypeError):
                        hourglass_data[dim].append(0.0)
                analyzed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            skipped_count += 1
            print(f"  Skipped: {item['id']} — {e}")

    print(f"  Analyzed: {analyzed_count}/{len(emotion_sentences)}")

    hourglass_metrics = {}
    for dim, values in hourglass_data.items():
        if values:
            hourglass_metrics[dim] = {
                "mean": round(statistics.mean(values), 2),
                "stdev": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "n": len(values),
            }
            print(f"  {dim:14s}: mean={hourglass_metrics[dim]['mean']:7.2f}  "
                  f"stdev={hourglass_metrics[dim]['stdev']:6.2f}  "
                  f"range=[{hourglass_metrics[dim]['min']}, {hourglass_metrics[dim]['max']}]")

    metrics["hourglass_distribution"] = hourglass_metrics
    raw_measurements.append({"test": "hourglass_distribution", "data": hourglass_metrics})

    # ── Save Results ──────────────────────────────────────────────
    await client.close()
    await pipeline.close()
    save_result("senticnet", metrics, raw_measurements)
    print("\n✓ SenticNet benchmark complete")


def run_benchmark():
    asyncio.run(_run_async())


if __name__ == "__main__":
    run_benchmark()

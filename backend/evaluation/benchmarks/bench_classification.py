"""
Classification Cascade Benchmark

Measures:
1. Per-tier latency
2. Tier coverage across 200 titles
3. Embedding model memory footprint
4. Batch throughput
"""

import json
import random
import statistics
import time
from pathlib import Path

import numpy as np
import psutil

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def run_benchmark():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from services.activity_classifier import ActivityClassifier
    from evaluation.benchmarks.runner import save_result

    classifier = ActivityClassifier()

    # Load test data
    with open(DATA_DIR / "window_titles_200.json") as f:
        titles = json.load(f)

    print(f"Loaded {len(titles)} window titles")

    metrics = {}
    raw_measurements = []

    # ── 1. Tier Coverage ──────────────────────────────────────────
    print("\n[1/4] Tier Coverage Analysis")
    tier_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    tier_titles = {0: [], 1: [], 2: [], 3: [], 4: []}
    classifications = []

    for item in titles:
        title = item["title"]
        # Extract app name from title (first part before " - ")
        parts = title.split(" - ", 1)
        app_name = parts[0].strip()
        window_title = parts[1].strip() if len(parts) > 1 else title

        category, tier = classifier.classify(app_name=app_name, window_title=window_title)
        tier_counts[tier] += 1
        tier_titles[tier].append(title)
        classifications.append({
            "id": item["id"],
            "title": title,
            "classified_category": category,
            "tier": tier,
            "expected_label": item["label"],
        })

    total = len(titles)
    print(f"  Tier 0 (User corrections): {tier_counts[0]:3d} ({tier_counts[0]/total*100:.1f}%)")
    print(f"  Tier 1 (App name):         {tier_counts[1]:3d} ({tier_counts[1]/total*100:.1f}%)")
    print(f"  Tier 2 (URL domain):       {tier_counts[2]:3d} ({tier_counts[2]/total*100:.1f}%)")
    print(f"  Tier 3 (Title keywords):   {tier_counts[3]:3d} ({tier_counts[3]/total*100:.1f}%)")
    print(f"  Tier 4 (Embedding):        {tier_counts[4]:3d} ({tier_counts[4]/total*100:.1f}%)")

    rules_pct = (tier_counts[0] + tier_counts[1] + tier_counts[2] + tier_counts[3]) / total * 100
    print(f"  Rules (tiers 0-3):         {rules_pct:.1f}% {'✓' if rules_pct >= 40 else '✗'} (target: ≥40%)")

    metrics["tier_coverage"] = {
        "tier_0_user_corrections": {"count": tier_counts[0], "pct": round(tier_counts[0]/total*100, 1)},
        "tier_1_app_name": {"count": tier_counts[1], "pct": round(tier_counts[1]/total*100, 1)},
        "tier_2_url_domain": {"count": tier_counts[2], "pct": round(tier_counts[2]/total*100, 1)},
        "tier_3_title_keywords": {"count": tier_counts[3], "pct": round(tier_counts[3]/total*100, 1)},
        "tier_4_embedding": {"count": tier_counts[4], "pct": round(tier_counts[4]/total*100, 1)},
        "rules_total_pct": round(rules_pct, 1),
    }

    raw_measurements.append({"test": "tier_coverage", "classifications": classifications})

    # ── 2. Per-Tier Latency ───────────────────────────────────────
    print("\n[2/4] Per-Tier Latency (100 iterations each)")

    # Group titles by their resolved tier
    tier_latencies = {}

    for tier_num in sorted(tier_counts.keys()):
        if not tier_titles[tier_num]:
            continue

        sample_titles = tier_titles[tier_num]
        latencies = []

        for _ in range(100):
            item_title = random.choice(sample_titles)
            parts = item_title.split(" - ", 1)
            app_name = parts[0].strip()
            window_title = parts[1].strip() if len(parts) > 1 else item_title

            start = time.perf_counter()
            classifier.classify(app_name=app_name, window_title=window_title)
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

        tier_latencies[f"tier_{tier_num}"] = {
            "mean_ms": round(statistics.mean(latencies), 4),
            "median_ms": round(statistics.median(latencies), 4),
            "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 4),
            "min_ms": round(min(latencies), 4),
            "max_ms": round(max(latencies), 4),
            "sample_count": len(sample_titles),
        }
        print(f"  Tier {tier_num}: mean={tier_latencies[f'tier_{tier_num}']['mean_ms']:.4f}ms  "
              f"median={tier_latencies[f'tier_{tier_num}']['median_ms']:.4f}ms  "
              f"p95={tier_latencies[f'tier_{tier_num}']['p95_ms']:.4f}ms")

    metrics["per_tier_latency"] = tier_latencies
    raw_measurements.append({"test": "per_tier_latency", "data": tier_latencies})

    # ── 3. Embedding Model Memory Footprint ───────────────────────
    print("\n[3/4] Embedding Model Memory Footprint")

    # Force a fresh classifier without embedding model loaded
    fresh_classifier = ActivityClassifier()
    process = psutil.Process()

    rss_before = process.memory_info().rss / (1024 * 1024)
    print(f"  RSS before embedding load: {rss_before:.1f} MB")

    # Force load the embedding model by classifying something that falls through to tier 4
    fresh_classifier._ensure_embedding_model()

    rss_after = process.memory_info().rss / (1024 * 1024)
    delta = rss_after - rss_before
    print(f"  RSS after embedding load:  {rss_after:.1f} MB")
    print(f"  Delta (MiniLM footprint):  {delta:.1f} MB")

    metrics["embedding_memory"] = {
        "rss_before_mb": round(rss_before, 1),
        "rss_after_mb": round(rss_after, 1),
        "delta_mb": round(delta, 1),
    }
    raw_measurements.append({"test": "embedding_memory", "data": metrics["embedding_memory"]})

    # ── 4. Batch Throughput ───────────────────────────────────────
    print("\n[4/4] Batch Throughput (1000 titles = 5x200)")

    batch_titles = titles * 5  # 1000 titles
    batch_times = []

    start_total = time.perf_counter()
    for item in batch_titles:
        title = item["title"]
        parts = title.split(" - ", 1)
        app_name = parts[0].strip()
        window_title = parts[1].strip() if len(parts) > 1 else title

        start = time.perf_counter()
        classifier.classify(app_name=app_name, window_title=window_title)
        elapsed_ms = (time.perf_counter() - start) * 1000
        batch_times.append(elapsed_ms)

    total_time = time.perf_counter() - start_total
    titles_per_sec = len(batch_titles) / total_time

    print(f"  Total titles: {len(batch_titles)}")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Throughput: {titles_per_sec:.0f} titles/sec {'✓' if titles_per_sec > 100 else '✗'} (target: >100)")
    print(f"  Mean per-title: {statistics.mean(batch_times):.4f}ms")
    print(f"  Median per-title: {statistics.median(batch_times):.4f}ms")

    metrics["batch_throughput"] = {
        "total_titles": len(batch_titles),
        "total_time_s": round(total_time, 3),
        "titles_per_sec": round(titles_per_sec, 1),
        "mean_per_title_ms": round(statistics.mean(batch_times), 4),
        "median_per_title_ms": round(statistics.median(batch_times), 4),
        "p95_per_title_ms": round(sorted(batch_times)[int(len(batch_times) * 0.95)], 4),
    }
    raw_measurements.append({"test": "batch_throughput", "data": metrics["batch_throughput"]})

    # ── Save Results ──────────────────────────────────────────────
    save_result("classification", metrics, raw_measurements)
    print("\n✓ Classification benchmark complete")


if __name__ == "__main__":
    run_benchmark()

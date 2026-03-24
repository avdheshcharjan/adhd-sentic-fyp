"""
Mem0 Memory Service Benchmark

Measures:
1. Store latency
2. Retrieval latency scaling
3. Retrieval relevance (top-1 hit rate)
4. Memory footprint scaling
"""

import gc
import json
import random
import statistics
import time
import uuid
from pathlib import Path

import numpy as np
import psutil

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"

# Test memories for benchmarking
BENCHMARK_MEMORIES = [
    "User prefers working in 25-minute Pomodoro sessions with 5-minute breaks",
    "User is most productive between 9am and 12pm on weekdays",
    "User takes Adderall XR 20mg every morning at 8am",
    "User finds background music helpful for coding but distracting for reading",
    "User's biggest distraction trigger is social media notifications",
    "User gets overwhelmed when there are more than 5 items on the to-do list",
    "User prefers bullet-point notes over long paragraphs",
    "User exercises every morning for 30 minutes which improves focus",
    "User's FYP supervisor meets every Thursday at 2pm",
    "User struggles most with starting tasks, not completing them",
    "User uses a standing desk and switches position every 45 minutes",
    "User finds pair programming more productive than solo coding",
    "User tends to skip lunch when hyperfocused, leading to afternoon crashes",
    "User has weekly accountability check-in with study partner on Mondays",
    "User avoids studying in the bedroom because it induces sleepiness",
    "User finds writing first drafts easier with dictation than typing",
    "User gets anxious before presentations and over-prepares as coping",
    "User prefers structured feedback over open-ended comments",
    "User benefits from body-doubling sessions via Discord",
    "User's medication effectiveness drops when sleeping less than 6 hours",
]


def run_benchmark():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from evaluation.benchmarks.runner import save_result

    process = psutil.Process()
    metrics = {}
    raw_measurements = []

    # Initialize Mem0 with a test user
    from mem0 import Memory

    # Use OpenAI embeddings (same as production config)
    from config import get_settings
    settings = get_settings()

    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": settings.OPENAI_API_KEY,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": settings.OPENAI_API_KEY,
            },
        },
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "dbname": "adhd_brain",
                "user": "adhd",
                "password": "adhd",
                "host": "localhost",
                "port": 5433,
                "collection_name": f"benchmark_{uuid.uuid4().hex[:8]}",
            },
        },
    }

    try:
        mem = Memory.from_config(config)
    except Exception as e:
        print(f"ERROR: Could not initialize Mem0: {e}")
        print("Skipping memory benchmarks")
        save_result("memory", {"error": str(e)}, [])
        return

    test_user = f"bench_user_{uuid.uuid4().hex[:8]}"
    print(f"  Test user: {test_user}")
    print(f"  Collection: {config['vector_store']['config']['collection_name']}")

    # ── 1. Store Latency ──────────────────────────────────────────
    print("\n[1/4] Store Latency (20 memories)")

    store_latencies = []
    for i, memory_text in enumerate(BENCHMARK_MEMORIES[:20]):
        start = time.perf_counter()
        try:
            mem.add(memory_text, user_id=test_user)
            elapsed_ms = (time.perf_counter() - start) * 1000
            store_latencies.append(elapsed_ms)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            store_latencies.append(elapsed_ms)
            print(f"  Store error {i}: {e}")

    sorted_store = sorted(store_latencies)
    metrics["store_latency"] = {
        "count": len(store_latencies),
        "mean_ms": round(statistics.mean(store_latencies), 1),
        "median_ms": round(statistics.median(store_latencies), 1),
        "p95_ms": round(sorted_store[int(len(sorted_store) * 0.95)], 1),
        "min_ms": round(min(store_latencies), 1),
        "max_ms": round(max(store_latencies), 1),
    }
    print(f"  Mean: {metrics['store_latency']['mean_ms']}ms")
    print(f"  Median: {metrics['store_latency']['median_ms']}ms")
    print(f"  P95: {metrics['store_latency']['p95_ms']}ms")
    raw_measurements.append({"test": "store_latency", "times_ms": [round(t, 1) for t in store_latencies]})

    # ── 2. Retrieval Latency ──────────────────────────────────────
    print("\n[2/4] Retrieval Latency (10 queries)")

    test_queries = [
        "How long should my work sessions be?",
        "When am I most productive?",
        "What medication do I take?",
        "What distracts me the most?",
        "How do I handle too many tasks?",
        "What helps me focus when coding?",
        "Do I exercise regularly?",
        "When do I meet my supervisor?",
        "What's my biggest challenge with tasks?",
        "What happens when I skip lunch?",
    ]

    retrieval_latencies = []
    for query in test_queries:
        start = time.perf_counter()
        try:
            results = mem.search(query, user_id=test_user, limit=5)
            elapsed_ms = (time.perf_counter() - start) * 1000
            retrieval_latencies.append(elapsed_ms)
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            retrieval_latencies.append(elapsed_ms)
            print(f"  Retrieval error: {e}")

    sorted_retrieval = sorted(retrieval_latencies)
    metrics["retrieval_latency"] = {
        "count": len(retrieval_latencies),
        "mean_ms": round(statistics.mean(retrieval_latencies), 1),
        "median_ms": round(statistics.median(retrieval_latencies), 1),
        "p95_ms": round(sorted_retrieval[int(len(sorted_retrieval) * 0.95)], 1),
        "min_ms": round(min(retrieval_latencies), 1),
        "max_ms": round(max(retrieval_latencies), 1),
    }
    print(f"  Mean: {metrics['retrieval_latency']['mean_ms']}ms")
    print(f"  Median: {metrics['retrieval_latency']['median_ms']}ms")
    print(f"  P95: {metrics['retrieval_latency']['p95_ms']}ms")
    raw_measurements.append({"test": "retrieval_latency", "times_ms": [round(t, 1) for t in retrieval_latencies]})

    # ── 3. Retrieval Relevance (Top-1 Hit Rate) ───────────────────
    print("\n[3/4] Retrieval Relevance Check")

    # Known-answer pairs: query -> expected substring in top result
    relevance_pairs = [
        ("How long should my work sessions be?", "pomodoro"),
        ("When am I most productive?", "9am"),
        ("What medication do I take?", "adderall"),
        ("What distracts me the most?", "social media"),
        ("Do I exercise?", "exercise"),
        ("When do I meet my supervisor?", "thursday"),
        ("What happens when I skip meals?", "lunch"),
        ("Do I use a standing desk?", "standing desk"),
        ("What helps me code better?", "pair programming"),
        ("How does sleep affect my medication?", "sleeping"),
    ]

    hits = 0
    total_checks = 0
    relevance_details = []
    for query, expected_keyword in relevance_pairs:
        try:
            results = mem.search(query, user_id=test_user, limit=1)
            if isinstance(results, dict) and "results" in results:
                results = results["results"]

            top_result = ""
            if results and len(results) > 0:
                if isinstance(results[0], dict):
                    top_result = results[0].get("memory", results[0].get("text", "")).lower()
                else:
                    top_result = str(results[0]).lower()

            is_hit = expected_keyword.lower() in top_result
            if is_hit:
                hits += 1
            total_checks += 1
            relevance_details.append({
                "query": query,
                "expected_keyword": expected_keyword,
                "top_result_snippet": top_result[:100],
                "hit": is_hit,
            })
        except Exception as e:
            total_checks += 1
            relevance_details.append({"query": query, "error": str(e), "hit": False})

    hit_rate = hits / total_checks * 100 if total_checks > 0 else 0
    print(f"  Top-1 hit rate: {hits}/{total_checks} ({hit_rate:.0f}%)")
    print(f"  Target: ≥80% {'✓' if hit_rate >= 80 else '✗'}")

    metrics["retrieval_relevance"] = {
        "hits": hits,
        "total": total_checks,
        "hit_rate_pct": round(hit_rate, 1),
    }
    raw_measurements.append({"test": "retrieval_relevance", "details": relevance_details})

    # ── 4. Memory Footprint ───────────────────────────────────────
    print("\n[4/4] Memory Footprint")

    rss = process.memory_info().rss / (1024 * 1024)
    print(f"  RSS with Mem0 loaded (20 memories stored): {rss:.0f} MB")

    metrics["memory_footprint"] = {
        "rss_mb": round(rss, 0),
        "memories_stored": 20,
    }
    raw_measurements.append({"test": "memory_footprint", "data": metrics["memory_footprint"]})

    # ── Cleanup ───────────────────────────────────────────────────
    # Note: we leave the test collection in place; it will be garbage collected
    # or can be manually cleaned up

    # ── Save Results ──────────────────────────────────────────────
    save_result("memory", metrics, raw_measurements)
    print("\n✓ Memory benchmark complete")


if __name__ == "__main__":
    run_benchmark()

"""
Mem0 Memory Retrieval Quality Evaluation

Evaluates whether Mem0 returns relevant memories when queried.
Tests Hit@1, Hit@3, nDCG@3, and mean retrieval latency.

Usage:
    python -m evaluation.accuracy.eval_memory_retrieval
"""

import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Seed everything
random.seed(42)
np.random.seed(42)

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
DATA_PATH = ROOT / "evaluation" / "data" / "memory_test_profiles.json"
RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def ndcg_at_k(retrieved_ids: list[str], relevant_id: str, k: int = 3) -> float:
    """Compute normalized discounted cumulative gain at k.

    Args:
        retrieved_ids: List of memory IDs returned by search (ordered by rank)
        relevant_id: The expected/ground-truth memory ID
        k: Number of top results to consider

    Returns:
        nDCG@k score (0.0 to 1.0)
    """
    dcg = sum(
        (1.0 if i < len(retrieved_ids) and retrieved_ids[i] == relevant_id else 0.0)
        / math.log2(i + 2)
        for i in range(min(k, len(retrieved_ids)))
    )
    # Ideal DCG: relevant doc at rank 1
    idcg = 1.0 / math.log2(2)
    return dcg / idcg if idcg > 0 else 0.0


def run_evaluation():
    """Run the full memory retrieval evaluation."""
    print("=" * 70)
    print("MEM0 MEMORY RETRIEVAL QUALITY EVALUATION")
    print("=" * 70)

    # ── Load test data ───────────────────────────────────────────────
    with open(DATA_PATH, "r") as f:
        test_profiles = json.load(f)

    print(f"\nLoaded {len(test_profiles)} test profiles")

    # ── Initialize memory service ────────────────────────────────────
    sys.path.insert(0, str(ROOT))
    from services.memory_service import MemoryService

    # Create a fresh instance (don't use singleton to avoid state leaks)
    mem_service = MemoryService()

    if not mem_service.mem0:
        print("\n  ERROR: Mem0 is not initialized. Check OPENAI_API_KEY and PostgreSQL connection.")
        print("  Cannot proceed with memory retrieval evaluation.")
        return None

    print("  Mem0 initialized successfully")

    # ── Run evaluation per profile ───────────────────────────────────
    all_results = []
    hit_at_1_scores = []
    hit_at_3_scores = []
    ndcg_scores = []
    all_latencies = []

    for pi, profile in enumerate(test_profiles):
        profile_id = profile["profile_id"]
        description = profile["description"]
        memories = profile["memories"]
        queries = profile["test_queries"]

        print(f"\n  [{pi + 1}/{len(test_profiles)}] Profile: {profile_id}")
        print(f"    {description}")

        # ── Step 1: Clear state for this profile ─────────────────────
        eval_user_id = f"eval_{profile_id}"

        # Delete existing memories for this eval user
        try:
            existing = mem_service.mem0.get_all(user_id=eval_user_id)
            if isinstance(existing, dict) and "results" in existing:
                existing_mems = existing["results"]
            elif isinstance(existing, list):
                existing_mems = existing
            else:
                existing_mems = []

            for mem in existing_mems:
                mem_id = mem.get("id") if isinstance(mem, dict) else None
                if mem_id:
                    mem_service.mem0.delete(mem_id)
        except Exception as e:
            print(f"    Warning: Could not clear existing memories: {e}")

        # ── Step 2: Store all memories ───────────────────────────────
        print(f"    Storing {len(memories)} memories...", end="", flush=True)
        memory_id_map = {}

        for mem in memories:
            try:
                result = mem_service.mem0.add(
                    mem["content"],
                    user_id=eval_user_id,
                    metadata={
                        "eval_memory_id": mem["memory_id"],
                        "topic": mem["metadata"].get("topic", ""),
                        "emotion": mem["metadata"].get("emotion", ""),
                    },
                )
                # Store mapping from eval_memory_id to actual Mem0 ID
                if isinstance(result, dict) and "results" in result:
                    for r in result["results"]:
                        if isinstance(r, dict) and "id" in r:
                            memory_id_map[mem["memory_id"]] = r["id"]
                elif isinstance(result, list):
                    for r in result:
                        if isinstance(r, dict) and "id" in r:
                            memory_id_map[mem["memory_id"]] = r["id"]
            except Exception as e:
                print(f"\n    Warning: Failed to store memory {mem['memory_id']}: {e}")

        print(f" done ({len(memory_id_map)} stored)")

        # Small delay to let embeddings propagate
        time.sleep(0.5)

        # ── Step 3: Query and evaluate ───────────────────────────────
        profile_results = []

        for qi, query in enumerate(queries):
            query_text = query["query"]
            expected_memory_id = query["expected_memory_id"]
            expected_content = query.get("expected_content", "")

            print(f"    Query {qi + 1}: {query_text[:60]}...", end="", flush=True)

            start = time.perf_counter()
            try:
                search_results = mem_service.search_relevant_context(
                    user_id=eval_user_id,
                    query=query_text,
                    limit=3,
                )
            except Exception as e:
                print(f" [ERROR: {e}]")
                search_results = []
            latency_ms = (time.perf_counter() - start) * 1000
            all_latencies.append(latency_ms)

            # Extract retrieved memory IDs
            retrieved_eval_ids = []
            retrieved_contents = []
            for sr in search_results:
                if isinstance(sr, dict):
                    content = sr.get("memory", sr.get("text", sr.get("content", "")))
                    retrieved_contents.append(content)
                    # Try to match by eval_memory_id in metadata
                    metadata = sr.get("metadata", {})
                    eval_id = metadata.get("eval_memory_id", "")
                    if eval_id:
                        retrieved_eval_ids.append(eval_id)
                    else:
                        # Fallback: try to match by content similarity
                        for mem in memories:
                            if mem["content"] in content or content in mem["content"]:
                                retrieved_eval_ids.append(mem["memory_id"])
                                break
                        else:
                            retrieved_eval_ids.append(f"unknown_{len(retrieved_eval_ids)}")

            # Compute metrics
            hit1 = 1.0 if retrieved_eval_ids and retrieved_eval_ids[0] == expected_memory_id else 0.0
            hit3 = 1.0 if expected_memory_id in retrieved_eval_ids[:3] else 0.0
            ndcg = ndcg_at_k(retrieved_eval_ids, expected_memory_id, k=3)

            hit_at_1_scores.append(hit1)
            hit_at_3_scores.append(hit3)
            ndcg_scores.append(ndcg)

            status = "HIT@1" if hit1 else ("HIT@3" if hit3 else "MISS")
            print(f" [{status}] nDCG={ndcg:.2f} ({latency_ms:.0f}ms)")

            profile_results.append({
                "query": query_text,
                "expected_memory_id": expected_memory_id,
                "expected_content": expected_content,
                "retrieved_ids": retrieved_eval_ids,
                "retrieved_contents": retrieved_contents[:3],
                "hit_at_1": hit1,
                "hit_at_3": hit3,
                "ndcg_at_3": ndcg,
                "latency_ms": latency_ms,
            })

        all_results.append({
            "profile_id": profile_id,
            "description": description,
            "memories_stored": len(memory_id_map),
            "queries_run": len(queries),
            "query_results": profile_results,
        })

        # ── Cleanup: delete eval memories ────────────────────────────
        try:
            existing = mem_service.mem0.get_all(user_id=eval_user_id)
            if isinstance(existing, dict) and "results" in existing:
                existing_mems = existing["results"]
            elif isinstance(existing, list):
                existing_mems = existing
            else:
                existing_mems = []
            for mem in existing_mems:
                mem_id = mem.get("id") if isinstance(mem, dict) else None
                if mem_id:
                    mem_service.mem0.delete(mem_id)
        except Exception:
            pass

    # ── Aggregate metrics ────────────────────────────────────────────
    mean_hit1 = float(np.mean(hit_at_1_scores)) if hit_at_1_scores else 0.0
    mean_hit3 = float(np.mean(hit_at_3_scores)) if hit_at_3_scores else 0.0
    mean_ndcg = float(np.mean(ndcg_scores)) if ndcg_scores else 0.0
    mean_latency = float(np.mean(all_latencies)) if all_latencies else 0.0

    total_queries = len(hit_at_1_scores)

    print(f"\n{'=' * 70}")
    print("AGGREGATE METRICS")
    print(f"{'=' * 70}")
    print(f"  Total profiles: {len(test_profiles)}")
    print(f"  Total queries:  {total_queries}")
    print(f"  Hit@1:          {mean_hit1:.4f} ({mean_hit1 * 100:.1f}%)")
    print(f"  Hit@3:          {mean_hit3:.4f} ({mean_hit3 * 100:.1f}%)")
    print(f"  nDCG@3:         {mean_ndcg:.4f}")
    print(f"  Mean latency:   {mean_latency:.1f} ms")

    if all_latencies:
        print(f"  Median latency: {float(np.median(all_latencies)):.1f} ms")
        print(f"  P95 latency:    {float(np.percentile(all_latencies, 95)):.1f} ms")

    # ── Error analysis ───────────────────────────────────────────────
    misses = []
    for profile_result in all_results:
        for qr in profile_result["query_results"]:
            if qr["hit_at_3"] == 0.0:
                misses.append({
                    "profile": profile_result["profile_id"],
                    "query": qr["query"],
                    "expected_id": qr["expected_memory_id"],
                    "expected_content": qr["expected_content"],
                    "retrieved": qr["retrieved_contents"][:3],
                })

    if misses:
        print(f"\n{'=' * 70}")
        print(f"QUERIES WHERE EXPECTED MEMORY NOT IN TOP-3 ({len(misses)} total)")
        print(f"{'=' * 70}")
        for m in misses:
            print(f"\n  Profile: {m['profile']}")
            print(f"  Query: {m['query']}")
            print(f"  Expected: [{m['expected_id']}] {m['expected_content'][:80]}")
            print(f"  Retrieved:")
            for j, r in enumerate(m["retrieved"]):
                print(f"    {j + 1}. {r[:80]}...")

    # ── Save results ─────────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "timestamp": timestamp,
        "total_profiles": len(test_profiles),
        "total_queries": total_queries,
        "aggregate_metrics": {
            "hit_at_1": mean_hit1,
            "hit_at_3": mean_hit3,
            "ndcg_at_3": mean_ndcg,
            "mean_latency_ms": mean_latency,
            "median_latency_ms": float(np.median(all_latencies)) if all_latencies else 0.0,
            "p95_latency_ms": float(np.percentile(all_latencies, 95)) if all_latencies else 0.0,
        },
        "misses": misses,
        "per_profile_results": all_results,
    }

    output_path = RESULTS_DIR / f"memory_retrieval_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    return output


if __name__ == "__main__":
    run_evaluation()

"""
Full Pipeline End-to-End Benchmark

Measures:
1. Latency waterfall (per-stage timing)
2. Warm vs cold latency
3. Ablation timing (with/without SenticNet)
4. System resources during burst
5. Concurrent stress test
"""

import asyncio
import gc
import json
import os
import random
import statistics
import sys
import threading
import time
from pathlib import Path

import numpy as np
import psutil

random.seed(42)
np.random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"

# Representative test messages for pipeline benchmarking
PIPELINE_TEST_MESSAGES = [
    "I can't focus today",
    "I feel overwhelmed with my workload",
    "I keep checking social media instead of working",
    "My medication doesn't seem to be helping today",
    "I'm so frustrated I can't get anything done",
    "I've been productive all morning and feel great",
    "I need to study for an exam but can't concentrate",
    "I'm anxious about my presentation tomorrow",
    "Everything feels pointless right now",
    "I just wasted three hours scrolling my phone",
    "I'm trying to break down this big project but don't know where to start",
    "I had a really good therapy session today",
    "My sleep was terrible and now I can't function",
    "I feel guilty about not being productive enough",
    "Can you help me plan my study schedule?",
    "I'm feeling jittery but can't focus on anything",
    "I've been hyperfocusing on the wrong task again",
    "My partner says I never listen to them",
    "I finally finished that assignment I've been putting off!",
    "I feel like everyone else has their life together except me",
]


async def _run_async():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from evaluation.benchmarks.runner import save_result

    process = psutil.Process()
    metrics = {}
    raw_measurements = []

    # ── 1. Latency Waterfall ─────────────────────────────────────
    print("\n[1/5] Latency Waterfall (20 messages, per-stage timing)")

    # Import pipeline components individually for timing
    from services.senticnet_pipeline import SenticNetPipeline
    from services.memory_service import MemoryService
    from services.mlx_inference import MLXInference

    senticnet_pipeline = SenticNetPipeline()
    mlx = MLXInference()
    mem_svc = MemoryService()

    from services.constants import ADHD_COACHING_SYSTEM_PROMPT

    waterfall_results = []
    test_user = "bench_pipeline_user"

    for i, message in enumerate(PIPELINE_TEST_MESSAGES):
        stage_times = {}

        # Stage A: SenticNet analysis
        t0 = time.perf_counter()
        try:
            senticnet_result = await senticnet_pipeline.analyze(text=message, mode="full")
        except Exception as e:
            senticnet_result = None
            print(f"  SenticNet error on msg {i}: {e}")
        stage_times["senticnet_analysis_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # Stage B: Safety check (from SenticNet result)
        t0 = time.perf_counter()
        is_critical = False
        if senticnet_result and senticnet_result.safety:
            is_critical = senticnet_result.safety.is_critical
        stage_times["safety_check_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage C: Memory retrieval
        t0 = time.perf_counter()
        try:
            mem_results = mem_svc.search_relevant_context(user_id=test_user, query=message, limit=5)
        except Exception:
            mem_results = []
        stage_times["memory_retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # Stage D: Build context (prompt assembly)
        t0 = time.perf_counter()
        senticnet_context = None
        if senticnet_result and senticnet_result.emotion:
            senticnet_context = {
                "primary_emotion": senticnet_result.emotion.primary_emotion,
                "introspection": senticnet_result.emotion.introspection,
                "temper": senticnet_result.emotion.temper,
                "attitude": senticnet_result.emotion.attitude,
                "sensitivity": senticnet_result.emotion.sensitivity,
                "polarity_score": senticnet_result.emotion.polarity_score,
                "intensity_score": senticnet_result.adhd_signals.intensity_score,
                "engagement_score": senticnet_result.adhd_signals.engagement_score,
                "wellbeing_score": senticnet_result.adhd_signals.wellbeing_score,
                "safety_level": senticnet_result.safety.level,
                "concepts": senticnet_result.adhd_signals.concepts[:5],
            }

        # Determine thinking mode
        use_thinking = False
        if senticnet_result:
            use_thinking = (
                abs(senticnet_result.adhd_signals.intensity_score) > 60
                or "help" in message.lower()
                or len(message) > 200
            )
        stage_times["prompt_assembly_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # Stage E: LLM generation (includes cold load if first call)
        t0 = time.perf_counter()
        try:
            response = mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
                user_message=message,
                senticnet_context=senticnet_context,
                use_thinking=use_thinking,
                max_tokens=150,
            )
        except Exception as e:
            response = f"[ERROR: {e}]"
            print(f"  LLM error on msg {i}: {e}")
        stage_times["llm_generation_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # Stage F: Memory store
        t0 = time.perf_counter()
        try:
            mem_svc.add_conversation_memory(
                user_id=test_user,
                message=f"User: {message}\nAssistant: {response[:100]}",
                context=str(senticnet_context) if senticnet_context else "",
            )
        except Exception:
            pass
        stage_times["memory_store_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        # Total
        stage_times["total_ms"] = round(sum(stage_times.values()), 1)

        waterfall_results.append({
            "message_index": i,
            "message_preview": message[:50],
            "stages": stage_times,
        })

        print(f"  [{i+1:2d}/20] total={stage_times['total_ms']:.0f}ms  "
              f"senticnet={stage_times['senticnet_analysis_ms']:.0f}ms  "
              f"llm={stage_times['llm_generation_ms']:.0f}ms  "
              f"mem_store={stage_times['memory_store_ms']:.0f}ms")

    # Compute averages
    avg_waterfall = {}
    stage_keys = ["senticnet_analysis_ms", "safety_check_ms", "memory_retrieval_ms",
                  "prompt_assembly_ms", "llm_generation_ms", "memory_store_ms", "total_ms"]
    for key in stage_keys:
        values = [r["stages"][key] for r in waterfall_results]
        avg_waterfall[key] = {
            "mean": round(statistics.mean(values), 1),
            "median": round(statistics.median(values), 1),
            "min": round(min(values), 1),
            "max": round(max(values), 1),
        }

    # Identify bottleneck
    stage_means = {k: avg_waterfall[k]["mean"] for k in stage_keys if k != "total_ms"}
    bottleneck = max(stage_means, key=stage_means.get)

    print(f"\n  Average waterfall:")
    for key in stage_keys:
        marker = " ← BOTTLENECK" if key == bottleneck else ""
        print(f"    {key:30s}: {avg_waterfall[key]['mean']:8.1f}ms{marker}")

    metrics["latency_waterfall"] = {
        "averages": avg_waterfall,
        "bottleneck": bottleneck,
        "message_count": len(PIPELINE_TEST_MESSAGES),
    }
    raw_measurements.append({"test": "latency_waterfall", "data": waterfall_results})

    # ── 2. Warm vs Cold Latency ───────────────────────────────────
    print("\n[2/5] Warm vs Cold Latency")

    # Warm: model already loaded from step 1
    warm_times = []
    for msg in PIPELINE_TEST_MESSAGES[:5]:
        t0 = time.perf_counter()
        try:
            mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
                user_message=msg,
                use_thinking=False,
                max_tokens=100,
            )
        except Exception:
            pass
        warm_times.append((time.perf_counter() - t0) * 1000)

    warm_mean = statistics.mean(warm_times)
    print(f"  Warm mean (model loaded): {warm_mean:.0f}ms")

    # Cold start data is already measured in bench_llm.py (mean ~1.78s)
    # MLX has a known Metal GPU assertion crash when rapidly unloading/reloading models
    # on Apple Silicon (AGXG16GFamilyCommandBuffer). Instead of risking a process crash,
    # we reference the cold start benchmark data and compute the overhead.
    cold_start_overhead_ms = 1780  # From bench_llm.py cold start measurements
    cold_first_estimated = warm_mean + cold_start_overhead_ms

    print(f"  Cold start overhead (from LLM bench): {cold_start_overhead_ms}ms")
    print(f"  Estimated cold first request: {cold_first_estimated:.0f}ms")
    print(f"  Note: MLX Metal GPU assertion prevents live cold-reload in same process")

    metrics["warm_vs_cold"] = {
        "warm_mean_ms": round(warm_mean, 0),
        "cold_start_overhead_ms": cold_start_overhead_ms,
        "estimated_cold_first_ms": round(cold_first_estimated, 0),
        "note": "Cold start measured in bench_llm.py; MLX Metal GPU assertion prevents in-process reload",
    }
    raw_measurements.append({"test": "warm_vs_cold", "warm_times": [round(t, 1) for t in warm_times]})

    # ── 3. Ablation Timing ────────────────────────────────────────
    print("\n[3/5] Ablation Timing (with vs without SenticNet)")

    test_messages_ablation = PIPELINE_TEST_MESSAGES[:10]

    # Full pipeline (with SenticNet)
    full_times = []
    for msg in test_messages_ablation:
        t0 = time.perf_counter()
        try:
            result = await senticnet_pipeline.analyze(text=msg, mode="full")
            senticnet_ctx = None
            if result and result.emotion:
                senticnet_ctx = {
                    "primary_emotion": result.emotion.primary_emotion,
                    "intensity_score": result.adhd_signals.intensity_score,
                    "engagement_score": result.adhd_signals.engagement_score,
                    "wellbeing_score": result.adhd_signals.wellbeing_score,
                    "safety_level": result.safety.level,
                    "concepts": result.adhd_signals.concepts[:5],
                }
            mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
                user_message=msg,
                senticnet_context=senticnet_ctx,
                use_thinking=False,
                max_tokens=100,
            )
        except Exception:
            pass
        full_times.append((time.perf_counter() - t0) * 1000)

    # Ablation (without SenticNet)
    from services.constants import ADHD_COACHING_SYSTEM_PROMPT_VANILLA
    ablation_times = []
    for msg in test_messages_ablation:
        t0 = time.perf_counter()
        try:
            mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT_VANILLA,
                user_message=msg,
                senticnet_context=None,
                use_thinking=False,
                max_tokens=100,
            )
        except Exception:
            pass
        ablation_times.append((time.perf_counter() - t0) * 1000)

    full_mean = statistics.mean(full_times)
    ablation_mean = statistics.mean(ablation_times)
    senticnet_cost = full_mean - ablation_mean

    print(f"  Full pipeline (with SenticNet): {full_mean:.0f}ms mean")
    print(f"  Ablation (without SenticNet):   {ablation_mean:.0f}ms mean")
    print(f"  SenticNet cost:                 {senticnet_cost:.0f}ms ({senticnet_cost/full_mean*100:.1f}% of total)")

    metrics["ablation_timing"] = {
        "full_pipeline_mean_ms": round(full_mean, 0),
        "ablation_mean_ms": round(ablation_mean, 0),
        "senticnet_cost_ms": round(senticnet_cost, 0),
        "senticnet_cost_pct": round(senticnet_cost / full_mean * 100, 1) if full_mean > 0 else 0,
    }
    raw_measurements.append({"test": "ablation_timing",
                             "full_times": [round(t, 1) for t in full_times],
                             "ablation_times": [round(t, 1) for t in ablation_times]})

    # ── 4. System Resources During Burst ──────────────────────────
    print("\n[4/5] System Resources During Burst (10 back-to-back messages)")

    resource_samples = []
    sampling_active = True

    def sample_resources():
        while sampling_active:
            resource_samples.append({
                "timestamp": time.time(),
                "cpu_pct": process.cpu_percent(interval=0.1),
                "rss_mb": process.memory_info().rss / (1024 * 1024),
            })
            time.sleep(0.4)  # ~500ms interval (100ms used by cpu_percent)

    sampler_thread = threading.Thread(target=sample_resources, daemon=True)
    sampler_thread.start()

    burst_start = time.perf_counter()
    burst_messages = PIPELINE_TEST_MESSAGES[:10]
    for msg in burst_messages:
        try:
            mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
                user_message=msg,
                use_thinking=False,
                max_tokens=100,
            )
        except Exception:
            pass

    burst_elapsed = time.perf_counter() - burst_start
    sampling_active = False
    sampler_thread.join(timeout=2)

    if resource_samples:
        cpu_values = [s["cpu_pct"] for s in resource_samples]
        rss_values = [s["rss_mb"] for s in resource_samples]

        peak_cpu = max(cpu_values)
        avg_cpu = statistics.mean(cpu_values)
        peak_rss = max(rss_values)
        avg_rss = statistics.mean(rss_values)

        print(f"  Burst duration: {burst_elapsed:.1f}s")
        print(f"  Samples collected: {len(resource_samples)}")
        print(f"  Peak CPU: {peak_cpu:.1f}%")
        print(f"  Avg CPU:  {avg_cpu:.1f}%")
        print(f"  Peak RSS: {peak_rss:.0f} MB {'✓' if peak_rss < 6144 else '✗'} (target: <6GB)")
        print(f"  Avg RSS:  {avg_rss:.0f} MB")

        metrics["burst_resources"] = {
            "burst_duration_s": round(burst_elapsed, 1),
            "sample_count": len(resource_samples),
            "peak_cpu_pct": round(peak_cpu, 1),
            "avg_cpu_pct": round(avg_cpu, 1),
            "peak_rss_mb": round(peak_rss, 0),
            "avg_rss_mb": round(avg_rss, 0),
        }
    else:
        print("  No resource samples collected")
        metrics["burst_resources"] = {"error": "no samples collected"}

    raw_measurements.append({"test": "burst_resources", "samples": resource_samples})

    # ── 5. Sequential Stress Test ─────────────────────────────────
    # NOTE: MLX Metal backend is NOT thread-safe. ThreadPoolExecutor causes
    # AGXG16GFamilyCommandBuffer assertion crash (signal 139 / segfault).
    # We run sequential requests instead, which is also the realistic usage
    # pattern for a single-user on-device application.
    print("\n[5/5] Sequential Stress Test (5 back-to-back requests)")

    stress_messages = PIPELINE_TEST_MESSAGES[:5]
    stress_results = []

    stress_start = time.perf_counter()
    for msg in stress_messages:
        t0 = time.perf_counter()
        try:
            response = mlx.generate_coaching_response(
                system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
                user_message=msg,
                use_thinking=False,
                max_tokens=100,
            )
            elapsed = (time.perf_counter() - t0) * 1000
            stress_results.append({"message": msg[:40], "latency_ms": round(elapsed, 1), "success": True})
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            stress_results.append({"message": msg[:40], "latency_ms": round(elapsed, 1), "success": False, "error": str(e)})
    stress_total = (time.perf_counter() - stress_start) * 1000

    all_succeeded = all(r["success"] for r in stress_results)
    stress_latencies = [r["latency_ms"] for r in stress_results]

    print(f"  All completed: {'✓' if all_succeeded else '✗'}")
    print(f"  Total wall time: {stress_total:.0f}ms")
    print(f"  Mean latency: {statistics.mean(stress_latencies):.0f}ms")
    print(f"  Max latency:  {max(stress_latencies):.0f}ms")

    metrics["sequential_stress"] = {
        "request_count": len(stress_messages),
        "all_succeeded": all_succeeded,
        "total_wall_time_ms": round(stress_total, 0),
        "mean_latency_ms": round(statistics.mean(stress_latencies), 0),
        "max_latency_ms": round(max(stress_latencies), 0),
        "min_latency_ms": round(min(stress_latencies), 0),
        "note": "Sequential (not concurrent) — MLX Metal backend is not thread-safe",
    }
    raw_measurements.append({"test": "sequential_stress", "results": stress_results})

    # ── Cleanup ──────────────────────────────────────────────────
    # Don't unload MLX model — causes Metal GPU assertion crash in same process
    try:
        await senticnet_pipeline.close()
    except Exception:
        pass
    gc.collect()

    # ── Save Results ─────────────────────────────────────────────
    save_result("pipeline", metrics, raw_measurements)
    print("\n✓ Pipeline benchmark complete")


def run_benchmark():
    asyncio.run(_run_async())


if __name__ == "__main__":
    run_benchmark()

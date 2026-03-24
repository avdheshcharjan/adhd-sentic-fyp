"""
Energy Benchmark (Apple Silicon via zeus-apple-silicon)

Measures:
1. Energy per LLM inference (CPU, GPU, DRAM, ANE in mJ)
2. Idle power with app running but no inference
3. Battery impact estimate
"""

import gc
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import psutil

random.seed(42)
np.random.seed(42)

SYSTEM_PROMPT = (
    "You are a supportive ADHD coach. Give brief, actionable advice. "
    "Under 3 sentences."
)

TEST_PROMPTS = [
    "I can't focus today",
    "I feel overwhelmed with my workload",
    "I keep checking social media instead of working",
    "My medication doesn't seem to be helping today",
    "I'm so frustrated I can't get anything done",
    "I've been productive all morning and feel great",
    "I need to study for an exam but can't concentrate",
    "I'm anxious about my presentation tomorrow",
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
    "Everything feels pointless right now",
]


def run_benchmark():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Try zeus-apple-silicon first
    try:
        from zeus_apple_silicon import AppleEnergyMonitor
        print("  Using zeus-apple-silicon for energy measurement")
        _run_with_zeus(AppleEnergyMonitor)
        return
    except ImportError:
        print("  zeus-apple-silicon not available")
    except Exception as e:
        print(f"  zeus-apple-silicon failed: {e}")

    # Fallback: psutil battery drain
    try:
        battery = psutil.sensors_battery()
        if battery is not None:
            print("  Using psutil battery drain estimation")
            _run_with_battery()
            return
        else:
            print("  No battery detected (plugged-in desktop?)")
    except Exception as e:
        print(f"  psutil battery failed: {e}")

    print("  ERROR: No energy measurement method available. Skipping.")
    from evaluation.benchmarks.runner import save_result
    save_result("energy", {"error": "No measurement method available"}, [])


def _run_with_zeus(AppleEnergyMonitor):
    from evaluation.benchmarks.runner import save_result
    from services.mlx_inference import MLXInference

    monitor = AppleEnergyMonitor()
    mlx = MLXInference()

    metrics = {}
    raw_measurements = []

    # ── 1. Idle Power (5 seconds, no inference) ────────────────────
    print("\n[1/3] Idle Power (5-second window, no inference)")

    monitor.begin_window("idle")
    time.sleep(5)
    idle_result = monitor.end_window("idle")

    idle_metrics = {
        "duration_s": 5,
        "cpu_total_mj": idle_result.cpu_total_mj,
        "gpu_mj": idle_result.gpu_mj,
        "dram_mj": idle_result.dram_mj,
        "ane_mj": idle_result.ane_mj,
        "total_mj": (idle_result.cpu_total_mj + idle_result.gpu_mj +
                     idle_result.dram_mj + idle_result.ane_mj),
    }
    # Convert to watts: W = mJ / (duration_ms)
    idle_watts = idle_metrics["total_mj"] / (5 * 1000)
    idle_metrics["estimated_watts"] = round(idle_watts, 2)

    print(f"  CPU: {idle_metrics['cpu_total_mj']} mJ")
    print(f"  GPU: {idle_metrics['gpu_mj']} mJ")
    print(f"  DRAM: {idle_metrics['dram_mj']} mJ")
    print(f"  ANE: {idle_metrics['ane_mj']} mJ")
    print(f"  Total: {idle_metrics['total_mj']} mJ ({idle_watts:.2f}W)")

    metrics["idle_power"] = idle_metrics
    raw_measurements.append({"test": "idle_power", "data": idle_metrics})

    # ── 2. Energy Per Inference (20 inferences) ───────────────────
    print("\n[2/3] Energy Per Inference (20 inferences)")

    # Warmup: ensure model is loaded
    print("  Warming up model...")
    mlx.generate_coaching_response(
        system_prompt=SYSTEM_PROMPT,
        user_message="warmup",
        use_thinking=False,
        max_tokens=50,
    )

    inference_energies = []
    for i, prompt in enumerate(TEST_PROMPTS[:20]):
        monitor.begin_window(f"inference_{i}")

        t0 = time.perf_counter()
        mlx.generate_coaching_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
            use_thinking=False,
            max_tokens=100,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        result = monitor.end_window(f"inference_{i}")

        total_mj = (result.cpu_total_mj + result.gpu_mj +
                    result.dram_mj + result.ane_mj)

        inference_energies.append({
            "prompt_index": i,
            "latency_ms": round(elapsed_ms, 1),
            "cpu_total_mj": result.cpu_total_mj,
            "gpu_mj": result.gpu_mj,
            "gpu_sram_mj": result.gpu_sram_mj,
            "dram_mj": result.dram_mj,
            "ane_mj": result.ane_mj,
            "total_mj": total_mj,
        })

        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/20] latency={elapsed_ms:.0f}ms  "
                  f"total={total_mj}mJ  gpu={result.gpu_mj}mJ  cpu={result.cpu_total_mj}mJ")

    # Compute statistics
    total_energies = [e["total_mj"] for e in inference_energies]
    gpu_energies = [e["gpu_mj"] for e in inference_energies]
    cpu_energies = [e["cpu_total_mj"] for e in inference_energies]
    dram_energies = [e["dram_mj"] for e in inference_energies]
    latencies = [e["latency_ms"] for e in inference_energies]

    per_inference = {
        "total_mj": {
            "mean": round(statistics.mean(total_energies), 1),
            "median": round(statistics.median(total_energies), 1),
            "min": min(total_energies),
            "max": max(total_energies),
            "stdev": round(statistics.stdev(total_energies), 1) if len(total_energies) > 1 else 0,
        },
        "gpu_mj": {
            "mean": round(statistics.mean(gpu_energies), 1),
            "median": round(statistics.median(gpu_energies), 1),
            "min": min(gpu_energies),
            "max": max(gpu_energies),
        },
        "cpu_mj": {
            "mean": round(statistics.mean(cpu_energies), 1),
            "median": round(statistics.median(cpu_energies), 1),
            "min": min(cpu_energies),
            "max": max(cpu_energies),
        },
        "dram_mj": {
            "mean": round(statistics.mean(dram_energies), 1),
            "median": round(statistics.median(dram_energies), 1),
            "min": min(dram_energies),
            "max": max(dram_energies),
        },
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 1),
            "median": round(statistics.median(latencies), 1),
        },
        "inference_count": len(inference_energies),
    }

    print(f"\n  Per-inference energy:")
    print(f"    Total:  mean={per_inference['total_mj']['mean']}mJ  "
          f"median={per_inference['total_mj']['median']}mJ")
    print(f"    GPU:    mean={per_inference['gpu_mj']['mean']}mJ")
    print(f"    CPU:    mean={per_inference['cpu_mj']['mean']}mJ")
    print(f"    DRAM:   mean={per_inference['dram_mj']['mean']}mJ")

    metrics["energy_per_inference"] = per_inference
    raw_measurements.append({"test": "energy_per_inference", "data": inference_energies})

    # ── 3. Battery Impact Estimate ─────────────────────────────────
    print("\n[3/3] Battery Impact Estimate")

    # M4 MacBook Pro battery: ~72.4 Wh = 72,400 mWh = 260,640,000 mJ
    BATTERY_CAPACITY_MJ = 260_640_000  # 72.4 Wh in mJ

    mean_energy_per_inference_mj = per_inference["total_mj"]["mean"]
    mean_latency_s = per_inference["latency_ms"]["mean"] / 1000

    # If user sends 1 message per minute (active coaching session)
    inferences_per_hour_active = 60
    # If user sends 1 message every 5 minutes (casual use)
    inferences_per_hour_casual = 12

    active_energy_per_hour_mj = mean_energy_per_inference_mj * inferences_per_hour_active
    casual_energy_per_hour_mj = mean_energy_per_inference_mj * inferences_per_hour_casual

    # Add idle energy
    idle_energy_per_hour_mj = idle_metrics["total_mj"] / 5 * 3600  # scale from 5s to 1h

    active_total_per_hour_mj = active_energy_per_hour_mj + idle_energy_per_hour_mj
    casual_total_per_hour_mj = casual_energy_per_hour_mj + idle_energy_per_hour_mj

    active_battery_hours = BATTERY_CAPACITY_MJ / active_total_per_hour_mj if active_total_per_hour_mj > 0 else 0
    casual_battery_hours = BATTERY_CAPACITY_MJ / casual_total_per_hour_mj if casual_total_per_hour_mj > 0 else 0

    battery_estimate = {
        "battery_capacity_wh": 72.4,
        "mean_energy_per_inference_mj": round(mean_energy_per_inference_mj, 1),
        "idle_energy_per_hour_mj": round(idle_energy_per_hour_mj, 0),
        "active_coaching": {
            "inferences_per_hour": inferences_per_hour_active,
            "inference_energy_per_hour_mj": round(active_energy_per_hour_mj, 0),
            "total_energy_per_hour_mj": round(active_total_per_hour_mj, 0),
            "estimated_battery_hours": round(active_battery_hours, 1),
        },
        "casual_use": {
            "inferences_per_hour": inferences_per_hour_casual,
            "inference_energy_per_hour_mj": round(casual_energy_per_hour_mj, 0),
            "total_energy_per_hour_mj": round(casual_total_per_hour_mj, 0),
            "estimated_battery_hours": round(casual_battery_hours, 1),
        },
    }

    print(f"  Battery capacity: 72.4 Wh ({BATTERY_CAPACITY_MJ / 1_000_000:.1f} kJ)")
    print(f"  Mean energy per inference: {mean_energy_per_inference_mj:.1f} mJ")
    print(f"  Idle energy per hour: {idle_energy_per_hour_mj:.0f} mJ")
    print(f"  Active coaching (60 inferences/hr): ~{active_battery_hours:.1f} hours battery life")
    print(f"  Casual use (12 inferences/hr):      ~{casual_battery_hours:.1f} hours battery life")

    metrics["battery_estimate"] = battery_estimate
    raw_measurements.append({"test": "battery_estimate", "data": battery_estimate})

    # ── Cleanup ──────────────────────────────────────────────────
    # Don't unload MLX — causes Metal GPU assertion crash
    gc.collect()

    # ── Save Results ─────────────────────────────────────────────
    save_result("energy", metrics, raw_measurements)
    print("\n✓ Energy benchmark complete")


def _run_with_battery():
    """Fallback: measure battery drain over inference burst using psutil."""
    from evaluation.benchmarks.runner import save_result
    from services.mlx_inference import MLXInference

    mlx = MLXInference()

    # Warmup
    mlx.generate_coaching_response(
        system_prompt=SYSTEM_PROMPT,
        user_message="warmup",
        use_thinking=False,
        max_tokens=50,
    )

    battery_before = psutil.sensors_battery()
    if not battery_before:
        save_result("energy", {"error": "No battery sensor"}, [])
        return

    start = time.perf_counter()
    for prompt in TEST_PROMPTS[:20]:
        mlx.generate_coaching_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=prompt,
            use_thinking=False,
            max_tokens=100,
        )
    elapsed = time.perf_counter() - start

    battery_after = psutil.sensors_battery()
    pct_drain = battery_before.percent - battery_after.percent

    metrics = {
        "method": "psutil_battery_drain",
        "inferences": 20,
        "duration_s": round(elapsed, 1),
        "battery_before_pct": battery_before.percent,
        "battery_after_pct": battery_after.percent,
        "drain_pct": round(pct_drain, 2),
        "note": "Low precision — battery percentage has ~1% granularity",
    }

    print(f"  Duration: {elapsed:.1f}s for 20 inferences")
    print(f"  Battery drain: {pct_drain:.2f}%")

    save_result("energy", metrics, [])
    print("\n✓ Energy benchmark complete (battery fallback)")


if __name__ == "__main__":
    run_benchmark()

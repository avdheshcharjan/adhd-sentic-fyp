"""
ADHD Second Brain Pipeline Benchmark Runner

Usage:
    python -m evaluation.benchmarks.runner --all
    python -m evaluation.benchmarks.runner --component llm
    python -m evaluation.benchmarks.runner --component classification
    python -m evaluation.benchmarks.runner --component senticnet
    python -m evaluation.benchmarks.runner --component memory
    python -m evaluation.benchmarks.runner --component pipeline
    python -m evaluation.benchmarks.runner --component energy
"""

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def get_system_info() -> dict:
    """Collect system information for benchmark context."""
    uname = platform.uname()
    mem = psutil.virtual_memory()

    info = {
        "os": f"macOS {platform.mac_ver()[0]}",
        "chip": uname.machine,
        "ram_gb": round(mem.total / (1024**3), 1),
        "python": sys.version.split()[0],
    }

    try:
        import mlx
        info["mlx_version"] = getattr(mlx, "__version__", "installed")
    except ImportError:
        info["mlx_version"] = "not installed"

    try:
        import mlx_lm
        info["mlx_lm_version"] = getattr(mlx_lm, "__version__", "installed")
    except ImportError:
        info["mlx_lm_version"] = "not installed"

    try:
        import sentence_transformers
        info["sentence_transformers_version"] = sentence_transformers.__version__
    except ImportError:
        info["sentence_transformers_version"] = "not installed"

    return info


def save_result(component: str, metrics: dict, raw_measurements: list) -> Path:
    """Save benchmark result to JSON file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "component": component,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_info": get_system_info(),
        "metrics": metrics,
        "raw_measurements": raw_measurements,
    }
    filepath = RESULTS_DIR / f"benchmark_{component}_{timestamp}.json"
    with open(filepath, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="ADHD Second Brain Benchmark Runner")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--component", type=str, help="Run specific component benchmark")
    args = parser.parse_args()

    if not args.all and not args.component:
        parser.print_help()
        return

    components = []
    if args.all:
        components = ["classification", "senticnet", "llm", "memory", "pipeline", "energy"]
    elif args.component:
        components = [args.component]

    print("=" * 60)
    print("ADHD Second Brain — Benchmark Runner")
    print("=" * 60)
    sys_info = get_system_info()
    for k, v in sys_info.items():
        print(f"  {k}: {v}")
    print("=" * 60)

    for component in components:
        print(f"\n{'─' * 60}")
        print(f"Running: {component}")
        print(f"{'─' * 60}")

        try:
            if component == "classification":
                from evaluation.benchmarks.bench_classification import run_benchmark
            elif component == "senticnet":
                from evaluation.benchmarks.bench_senticnet import run_benchmark
            elif component == "llm":
                from evaluation.benchmarks.bench_llm import run_benchmark
            elif component == "memory":
                from evaluation.benchmarks.bench_memory import run_benchmark
            elif component == "pipeline":
                from evaluation.benchmarks.bench_pipeline import run_benchmark
            elif component == "energy":
                from evaluation.benchmarks.bench_energy import run_benchmark
            else:
                print(f"Unknown component: {component}")
                continue

            run_benchmark()

        except Exception as e:
            print(f"ERROR running {component}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print("Benchmark run complete.")
    print(f"Results in: {RESULTS_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

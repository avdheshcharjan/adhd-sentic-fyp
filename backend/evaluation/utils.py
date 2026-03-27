"""Shared utilities for evaluation scripts."""

import json
import os
import platform
import random
import sys
import time
from datetime import datetime, timezone

import numpy as np


def seed_everything(seed: int = 42) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


def get_system_info() -> dict:
    """Collect system information for reproducibility."""
    info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "python": sys.version,
        "chip": platform.processor() or platform.machine(),
        "ram_gb": round(
            os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3), 1
        )
        if hasattr(os, "sysconf")
        else "unknown",
    }
    try:
        import mlx
        info["mlx_version"] = getattr(mlx, "__version__", "installed")
    except ImportError:
        info["mlx_version"] = "not installed"
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
    except ImportError:
        pass
    return info


def save_result(data: dict, prefix: str, results_dir: str = "evaluation/results") -> str:
    """Save evaluation result with timestamp."""
    os.makedirs(results_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
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

"""
Window Title Classification Accuracy Evaluation

Evaluates the 5-layer classification cascade against 200 labeled window titles.
Measures both granular category accuracy and 3-class productivity accuracy.

Usage:
    python -m evaluation.accuracy.eval_classification
"""

import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
    precision_recall_fscore_support,
)

# Seed everything
random.seed(42)
np.random.seed(42)

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
DATA_PATH = ROOT / "evaluation" / "data" / "window_titles_200.json"
RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Category → Productivity mapping ─────────────────────────────────
# Based on the test data's own labels, but we also need to map classifier output
PRODUCTIVE_CATEGORIES = {
    "development", "writing", "research", "design", "productivity",
}
NEUTRAL_CATEGORIES = {
    "communication", "system", "finance", "other", "browser",
}
DISTRACTING_CATEGORIES = {
    "social_media", "entertainment", "news", "shopping",
}


def category_to_productivity(category: str) -> str:
    """Map a granular category to productive/neutral/distracting."""
    if category in PRODUCTIVE_CATEGORIES:
        return "productive"
    if category in DISTRACTING_CATEGORIES:
        return "distracting"
    return "neutral"


KNOWN_BROWSERS = {
    "chrome", "google chrome", "safari", "firefox", "arc", "brave browser",
    "microsoft edge", "brave", "opera", "vivaldi",
}


def extract_app_name(title: str) -> str:
    """Extract app name from window title string.

    Titles look like:
        "Visual Studio Code - main.py — adhd-sentic-fyp"
        "Chrome - youtube.com - MrBeast: ..."
        "Terminal - python backend/main.py"
        "Steam - Counter-Strike 2"
    """
    # Split by ' - ' and take the first part as app name
    parts = title.split(" - ", 1)
    return parts[0].strip()


def extract_url_from_title(title: str, app_name: str) -> str | None:
    """Extract a URL/domain from browser window titles.

    Browser title patterns:
        "Chrome - github.com/user/repo - Pull Request #42"
        "Safari - docs.google.com - My Document"
        "Arc - youtube.com - Some Video Title"

    Returns the domain (e.g. "github.com") or None if not a browser.
    """
    if app_name.lower() not in KNOWN_BROWSERS:
        return None

    parts = title.split(" - ")
    if len(parts) < 2:
        return None

    # The second segment typically contains the domain/URL
    candidate = parts[1].strip()

    # Check if it looks like a domain (contains a dot, no spaces)
    if "." in candidate and " " not in candidate.split("/")[0]:
        # Return as a full URL so urlparse can extract the hostname
        return "https://" + candidate

    return None


def run_evaluation():
    """Run the full classification accuracy evaluation."""
    print("=" * 70)
    print("WINDOW TITLE CLASSIFICATION ACCURACY EVALUATION")
    print("=" * 70)

    # ── Load test data ───────────────────────────────────────────────
    with open(DATA_PATH, "r") as f:
        test_data = json.load(f)

    print(f"\nLoaded {len(test_data)} labeled window titles")

    # ── Initialize classifier ────────────────────────────────────────
    sys.path.insert(0, str(ROOT))
    from services.activity_classifier import ActivityClassifier

    classifier = ActivityClassifier()
    print("Classifier initialized")

    # ── Run classification ───────────────────────────────────────────
    predictions = []
    total_time = 0.0

    for item in test_data:
        title = item["title"]
        expected_category = item["label"]
        expected_productivity = item["productivity_label"]
        app_name = extract_app_name(title)
        url = extract_url_from_title(title, app_name)

        start = time.perf_counter()
        predicted_category, layer = classifier.classify(
            app_name=app_name,
            window_title=title,
            url=url,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        total_time += elapsed_ms

        predicted_productivity = category_to_productivity(predicted_category)

        predictions.append({
            "id": item["id"],
            "title": title,
            "app_name": app_name,
            "expected_category": expected_category,
            "predicted_category": predicted_category,
            "expected_productivity": expected_productivity,
            "predicted_productivity": predicted_productivity,
            "layer": layer,
            "latency_ms": elapsed_ms,
            "category_correct": predicted_category == expected_category,
            "productivity_correct": predicted_productivity == expected_productivity,
        })

    # ── Compute granular category metrics ────────────────────────────
    y_true_cat = [p["expected_category"] for p in predictions]
    y_pred_cat = [p["predicted_category"] for p in predictions]
    all_categories = sorted(set(y_true_cat) | set(y_pred_cat))

    cat_accuracy = accuracy_score(y_true_cat, y_pred_cat)
    cat_macro_f1 = f1_score(y_true_cat, y_pred_cat, average="macro", zero_division=0)
    cat_weighted_f1 = f1_score(y_true_cat, y_pred_cat, average="weighted", zero_division=0)
    cat_report = classification_report(
        y_true_cat, y_pred_cat, output_dict=True, zero_division=0
    )
    cat_cm = confusion_matrix(y_true_cat, y_pred_cat, labels=all_categories)

    # ── Compute productivity-level metrics ───────────────────────────
    y_true_prod = [p["expected_productivity"] for p in predictions]
    y_pred_prod = [p["predicted_productivity"] for p in predictions]
    prod_labels = ["productive", "neutral", "distracting"]

    prod_accuracy = accuracy_score(y_true_prod, y_pred_prod)
    prod_macro_f1 = f1_score(y_true_prod, y_pred_prod, average="macro", zero_division=0)
    prod_weighted_f1 = f1_score(y_true_prod, y_pred_prod, average="weighted", zero_division=0)
    prod_report = classification_report(
        y_true_prod, y_pred_prod, labels=prod_labels, output_dict=True, zero_division=0
    )
    prod_cm = confusion_matrix(y_true_prod, y_pred_prod, labels=prod_labels)

    # ── Per-layer accuracy ───────────────────────────────────────────
    layer_stats: dict[int, dict] = defaultdict(lambda: {"total": 0, "cat_correct": 0, "prod_correct": 0})
    for p in predictions:
        layer = p["layer"]
        layer_stats[layer]["total"] += 1
        if p["category_correct"]:
            layer_stats[layer]["cat_correct"] += 1
        if p["productivity_correct"]:
            layer_stats[layer]["prod_correct"] += 1

    per_layer = {}
    for layer_num in sorted(layer_stats.keys()):
        stats = layer_stats[layer_num]
        per_layer[f"layer_{layer_num}"] = {
            "total": stats["total"],
            "category_accuracy": stats["cat_correct"] / stats["total"] if stats["total"] > 0 else 0.0,
            "productivity_accuracy": stats["prod_correct"] / stats["total"] if stats["total"] > 0 else 0.0,
        }

    # ── Error analysis ───────────────────────────────────────────────
    category_errors = [p for p in predictions if not p["category_correct"]]
    productivity_errors = [p for p in predictions if not p["productivity_correct"]]

    # Group errors by pattern
    error_patterns: dict[str, list] = defaultdict(list)
    for err in productivity_errors:
        key = f"{err['expected_productivity']}_as_{err['predicted_productivity']}"
        error_patterns[key].append({
            "title": err["title"],
            "expected_cat": err["expected_category"],
            "predicted_cat": err["predicted_category"],
            "layer": err["layer"],
        })

    # ── Latency stats ────────────────────────────────────────────────
    latencies = [p["latency_ms"] for p in predictions]

    # ── Print results ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("GRANULAR CATEGORY CLASSIFICATION RESULTS")
    print("=" * 70)
    print(f"  Overall Accuracy: {cat_accuracy:.4f} ({cat_accuracy * 100:.1f}%)")
    print(f"  Macro-F1:         {cat_macro_f1:.4f}")
    print(f"  Weighted-F1:      {cat_weighted_f1:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_true_cat, y_pred_cat, zero_division=0))

    print("\n  Confusion Matrix (categories):")
    print(f"  Labels: {all_categories}")
    for i, row in enumerate(cat_cm):
        print(f"  {all_categories[i]:>15s}: {row.tolist()}")

    print("\n" + "=" * 70)
    print("PRODUCTIVITY-LEVEL (3-CLASS) RESULTS")
    print("=" * 70)
    print(f"  Overall Accuracy: {prod_accuracy:.4f} ({prod_accuracy * 100:.1f}%)")
    print(f"  Macro-F1:         {prod_macro_f1:.4f}")
    print(f"  Weighted-F1:      {prod_weighted_f1:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_true_prod, y_pred_prod, labels=prod_labels, zero_division=0))

    print("  Confusion Matrix (productivity):")
    print(f"  {'':>15s}  {'productive':>12s}  {'neutral':>12s}  {'distracting':>12s}")
    for i, label in enumerate(prod_labels):
        row = prod_cm[i].tolist()
        print(f"  {label:>15s}: {row[0]:>12d}  {row[1]:>12d}  {row[2]:>12d}")

    print("\n" + "=" * 70)
    print("PER-LAYER ACCURACY")
    print("=" * 70)
    layer_names = {
        0: "L0: User corrections",
        1: "L1: App name lookup",
        2: "L2: URL domain lookup",
        3: "L3: Title keywords",
        4: "L4: Embedding similarity",
    }
    for layer_key, stats in per_layer.items():
        layer_num = int(layer_key.split("_")[1])
        name = layer_names.get(layer_num, f"Layer {layer_num}")
        print(
            f"  {name:>25s}: {stats['total']:>3d} items | "
            f"Cat acc: {stats['category_accuracy']:.3f} | "
            f"Prod acc: {stats['productivity_accuracy']:.3f}"
        )

    print("\n" + "=" * 70)
    print(f"PRODUCTIVITY-LEVEL ERRORS ({len(productivity_errors)} total)")
    print("=" * 70)
    for pattern, errors in sorted(error_patterns.items()):
        print(f"\n  Pattern: {pattern} ({len(errors)} errors)")
        for err in errors[:5]:  # Show max 5 per pattern
            print(f"    - [{err['expected_cat']} -> {err['predicted_cat']}] L{err['layer']}: {err['title'][:80]}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")

    print("\n" + "=" * 70)
    print(f"CATEGORY-LEVEL ERRORS ({len(category_errors)} total)")
    print("=" * 70)
    for err in category_errors:
        print(
            f"  [{err['expected_category']:>15s} -> {err['predicted_category']:>15s}] "
            f"L{err['layer']}: {err['title'][:70]}"
        )

    print("\n" + "=" * 70)
    print("LATENCY STATISTICS")
    print("=" * 70)
    print(f"  Mean:   {np.mean(latencies):.3f} ms")
    print(f"  Median: {np.median(latencies):.3f} ms")
    print(f"  P95:    {np.percentile(latencies, 95):.3f} ms")
    print(f"  P99:    {np.percentile(latencies, 99):.3f} ms")
    print(f"  Max:    {np.max(latencies):.3f} ms")
    print(f"  Total:  {total_time:.1f} ms for {len(predictions)} items")

    # ── Save results JSON ────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = {
        "timestamp": timestamp,
        "dataset_size": len(test_data),
        "granular_category_metrics": {
            "accuracy": cat_accuracy,
            "macro_f1": cat_macro_f1,
            "weighted_f1": cat_weighted_f1,
            "per_class_report": cat_report,
            "confusion_matrix": {
                "labels": all_categories,
                "matrix": cat_cm.tolist(),
            },
        },
        "productivity_metrics": {
            "accuracy": prod_accuracy,
            "macro_f1": prod_macro_f1,
            "weighted_f1": prod_weighted_f1,
            "per_class_report": prod_report,
            "confusion_matrix": {
                "labels": prod_labels,
                "matrix": prod_cm.tolist(),
            },
        },
        "per_layer_accuracy": per_layer,
        "latency_stats": {
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "p99_ms": float(np.percentile(latencies, 99)),
            "max_ms": float(np.max(latencies)),
            "total_ms": total_time,
        },
        "error_analysis": {
            "category_error_count": len(category_errors),
            "productivity_error_count": len(productivity_errors),
            "error_patterns": {
                k: len(v) for k, v in error_patterns.items()
            },
            "category_errors": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "expected": e["expected_category"],
                    "predicted": e["predicted_category"],
                    "layer": e["layer"],
                }
                for e in category_errors
            ],
            "productivity_errors": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "expected": e["expected_productivity"],
                    "predicted": e["predicted_productivity"],
                    "expected_cat": e["expected_category"],
                    "predicted_cat": e["predicted_category"],
                    "layer": e["layer"],
                }
                for e in productivity_errors
            ],
        },
        "all_predictions": predictions,
    }

    output_path = RESULTS_DIR / f"classification_accuracy_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_evaluation()

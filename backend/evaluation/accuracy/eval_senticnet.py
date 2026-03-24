"""
SenticNet Emotion Detection Accuracy Evaluation

Evaluates whether SenticNet produces sensible emotion analysis for ADHD-relevant text.
Tests both the 6-category emotion classification and the Hourglass dimension correlations.

Usage:
    python -m evaluation.accuracy.eval_senticnet
"""

import asyncio
import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)

# Seed everything
random.seed(42)
np.random.seed(42)

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
DATA_PATH = ROOT / "evaluation" / "data" / "emotion_test_sentences.json"
RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Emotion category mapping ────────────────────────────────────────
# Maps SenticNet primary emotions to our 6 ADHD-relevant categories
EMOTION_TO_CATEGORY = {
    # Joyful
    "joy": "joyful",
    "happiness": "joyful",
    "ecstasy": "joyful",
    "delight": "joyful",
    "cheerfulness": "joyful",
    "excitement": "joyful",
    "bliss": "joyful",
    "elation": "joyful",
    "enthusiasm": "joyful",
    "relief": "joyful",
    "satisfaction": "joyful",
    "pride": "joyful",
    "admiration": "joyful",
    "gratitude": "joyful",
    "love": "joyful",
    "serenity": "joyful",
    "amusement": "joyful",
    "contentment": "joyful",
    "hope": "joyful",
    "optimism": "joyful",
    "pleasantness": "joyful",
    "calmness": "joyful",

    # Focused (engagement, interest, concentration)
    "interest": "focused",
    "anticipation": "focused",
    "curiosity": "focused",
    "vigilance": "focused",
    "surprise": "focused",
    "amazement": "focused",
    "trust": "focused",
    "acceptance": "focused",
    "responsiveness": "focused",
    "eagerness": "focused",

    # Frustrated (anger, irritation)
    "anger": "frustrated",
    "rage": "frustrated",
    "annoyance": "frustrated",
    "irritation": "frustrated",
    "contempt": "frustrated",
    "loathing": "frustrated",
    "disgust": "frustrated",
    "hostility": "frustrated",
    "aggressiveness": "frustrated",
    "frustration": "frustrated",
    "bitterness": "frustrated",
    "resentment": "frustrated",
    "dislike": "frustrated",

    # Anxious (fear, worry)
    "fear": "anxious",
    "terror": "anxious",
    "apprehension": "anxious",
    "anxiety": "anxious",
    "worry": "anxious",
    "nervousness": "anxious",
    "panic": "anxious",
    "dread": "anxious",
    "alarm": "anxious",

    # Disengaged (boredom, apathy)
    "boredom": "disengaged",
    "apathy": "disengaged",
    "indifference": "disengaged",
    "weariness": "disengaged",
    "tiredness": "disengaged",
    "pensiveness": "disengaged",
    "distraction": "disengaged",

    # Overwhelmed (sadness, helplessness)
    "sadness": "overwhelmed",
    "grief": "overwhelmed",
    "sorrow": "overwhelmed",
    "despair": "overwhelmed",
    "remorse": "overwhelmed",
    "shame": "overwhelmed",
    "guilt": "overwhelmed",
    "helplessness": "overwhelmed",
    "submission": "overwhelmed",
    "disapproval": "overwhelmed",
    "melancholy": "overwhelmed",
    "disappointment": "overwhelmed",

    # Default
    "unknown": "disengaged",
}


def map_emotion_to_category(primary_emotion: str) -> str:
    """Map a SenticNet primary emotion to one of 6 ADHD categories."""
    return EMOTION_TO_CATEGORY.get(primary_emotion.lower(), "disengaged")


def direction_to_numeric(direction: str) -> float:
    """Convert 'high'/'low' to 1.0/-1.0."""
    return 1.0 if direction == "high" else -1.0


async def run_evaluation():
    """Run the full SenticNet accuracy evaluation."""
    print("=" * 70)
    print("SENTICNET EMOTION DETECTION ACCURACY EVALUATION")
    print("=" * 70)

    # ── Load test data ───────────────────────────────────────────────
    with open(DATA_PATH, "r") as f:
        test_data = json.load(f)

    print(f"\nLoaded {len(test_data)} labeled test sentences")

    # ── Initialize SenticNet pipeline ────────────────────────────────
    sys.path.insert(0, str(ROOT))
    from services.senticnet_pipeline import SenticNetPipeline

    pipeline = SenticNetPipeline()
    print("SenticNet pipeline initialized")

    # ── Run analysis on each sentence ────────────────────────────────
    results_list = []
    failed_analyses = []
    total_time = 0.0

    for i, item in enumerate(test_data):
        sentence = item["sentence"]
        expected_emotion = item["expected_emotion"]
        expected_hourglass = item["expected_hourglass"]

        print(f"  [{i + 1}/{len(test_data)}] Analyzing: {sentence[:60]}...", end="", flush=True)

        start = time.perf_counter()
        try:
            result = await pipeline.analyze(text=sentence, mode="full")
            elapsed_ms = (time.perf_counter() - start) * 1000
            total_time += elapsed_ms

            # Extract primary emotion
            primary_emotion = result.emotion.primary_emotion
            predicted_category = map_emotion_to_category(primary_emotion)

            # Extract Hourglass dimensions
            hourglass_values = {
                "pleasantness": result.emotion.introspection,
                "attention": result.emotion.temper,
                "sensitivity": result.emotion.sensitivity,
                "aptitude": result.emotion.attitude,
            }

            has_result = primary_emotion != "unknown"

            results_list.append({
                "id": item["id"],
                "sentence": sentence,
                "expected_emotion": expected_emotion,
                "predicted_emotion_raw": primary_emotion,
                "predicted_emotion_category": predicted_category,
                "emotion_correct": predicted_category == expected_emotion,
                "has_result": has_result,
                "hourglass_actual": hourglass_values,
                "hourglass_expected": expected_hourglass,
                "emotion_details": result.emotion.emotion_details,
                "polarity": result.emotion.polarity,
                "intensity": result.adhd_signals.intensity_score,
                "engagement": result.adhd_signals.engagement_score,
                "wellbeing": result.adhd_signals.wellbeing_score,
                "latency_ms": elapsed_ms,
            })

            status = "OK" if predicted_category == expected_emotion else "MISS"
            print(f" [{status}] {primary_emotion} -> {predicted_category} (exp: {expected_emotion}) [{elapsed_ms:.0f}ms]")

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            total_time += elapsed_ms
            failed_analyses.append({
                "id": item["id"],
                "sentence": sentence,
                "error": str(e),
            })
            results_list.append({
                "id": item["id"],
                "sentence": sentence,
                "expected_emotion": expected_emotion,
                "predicted_emotion_raw": "error",
                "predicted_emotion_category": "disengaged",
                "emotion_correct": False,
                "has_result": False,
                "hourglass_actual": {"pleasantness": 0, "attention": 0, "sensitivity": 0, "aptitude": 0},
                "hourglass_expected": expected_hourglass,
                "emotion_details": "",
                "polarity": "neutral",
                "intensity": 0.0,
                "engagement": 0.0,
                "wellbeing": 0.0,
                "latency_ms": elapsed_ms,
            })
            print(f" [ERROR] {e}")

    await pipeline.close()

    # ── Coverage ─────────────────────────────────────────────────────
    items_with_results = [r for r in results_list if r["has_result"]]
    coverage_rate = len(items_with_results) / len(test_data) if test_data else 0.0

    print(f"\n{'=' * 70}")
    print(f"COVERAGE: {len(items_with_results)}/{len(test_data)} ({coverage_rate * 100:.1f}%)")
    print(f"{'=' * 70}")

    # ── Emotion classification metrics ───────────────────────────────
    y_true = [r["expected_emotion"] for r in results_list]
    y_pred = [r["predicted_emotion_category"] for r in results_list]
    emotion_labels = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]

    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=emotion_labels, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, labels=emotion_labels, average="weighted", zero_division=0)
    report = classification_report(
        y_true, y_pred, labels=emotion_labels, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=emotion_labels)

    print(f"\n{'=' * 70}")
    print("EMOTION CLASSIFICATION RESULTS (6 categories)")
    print(f"{'=' * 70}")
    print(f"  Accuracy:    {accuracy:.4f} ({accuracy * 100:.1f}%)")
    print(f"  Macro-F1:    {macro_f1:.4f}")
    print(f"  Weighted-F1: {weighted_f1:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_true, y_pred, labels=emotion_labels, zero_division=0))

    print("  Confusion Matrix:")
    header = f"  {'':>15s}" + "".join(f"  {l[:8]:>8s}" for l in emotion_labels)
    print(header)
    for i, label in enumerate(emotion_labels):
        row = cm[i].tolist()
        row_str = "".join(f"  {v:>8d}" for v in row)
        print(f"  {label:>15s}{row_str}")

    # ── Hourglass dimension correlations ─────────────────────────────
    dimensions = ["pleasantness", "attention", "sensitivity", "aptitude"]
    hourglass_correlations = {}

    print(f"\n{'=' * 70}")
    print("HOURGLASS DIMENSION CORRELATIONS (Spearman)")
    print(f"{'=' * 70}")

    for dim in dimensions:
        expected_dirs = [direction_to_numeric(r["hourglass_expected"][dim]) for r in results_list]
        actual_vals = [r["hourglass_actual"][dim] for r in results_list]

        if len(set(actual_vals)) > 1 and len(set(expected_dirs)) > 1:
            r, p = spearmanr(expected_dirs, actual_vals)
        else:
            r, p = 0.0, 1.0

        hourglass_correlations[dim] = {
            "spearman_r": float(r) if not np.isnan(r) else 0.0,
            "p_value": float(p) if not np.isnan(p) else 1.0,
            "significant": float(p) < 0.05 if not np.isnan(p) else False,
        }

        sig = "*" if float(p) < 0.05 else ""
        print(f"  {dim:>15s}: r = {r:.4f}, p = {p:.4f} {sig}")

    # ── Dimension distribution analysis ──────────────────────────────
    dimension_stats = {}
    low_variance_flags = []

    print(f"\n{'=' * 70}")
    print("HOURGLASS DIMENSION DISTRIBUTIONS")
    print(f"{'=' * 70}")

    for dim in dimensions:
        vals = [r["hourglass_actual"][dim] for r in results_list]
        stats = {
            "mean": float(np.mean(vals)),
            "stdev": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "range": float(np.max(vals) - np.min(vals)),
        }
        dimension_stats[dim] = stats

        flag = ""
        if stats["stdev"] < 0.05:
            flag = " [!!! LOW VARIANCE — SenticNet not differentiating]"
            low_variance_flags.append(dim)

        print(
            f"  {dim:>15s}: mean={stats['mean']:>7.2f}, std={stats['stdev']:>7.2f}, "
            f"range=[{stats['min']:>7.2f}, {stats['max']:>7.2f}]{flag}"
        )

    # ── Error analysis ───────────────────────────────────────────────
    errors = [r for r in results_list if not r["emotion_correct"]]

    print(f"\n{'=' * 70}")
    print(f"MISCLASSIFICATIONS ({len(errors)} / {len(results_list)})")
    print(f"{'=' * 70}")

    error_by_expected = defaultdict(list)
    for err in errors:
        error_by_expected[err["expected_emotion"]].append(err)

    for exp, errs in sorted(error_by_expected.items()):
        print(f"\n  Expected '{exp}' ({len(errs)} misclassified):")
        for e in errs:
            print(
                f"    -> predicted '{e['predicted_emotion_category']}' "
                f"(raw: {e['predicted_emotion_raw']}) | "
                f"{e['sentence'][:65]}..."
            )

    # ── Latency stats ────────────────────────────────────────────────
    latencies = [r["latency_ms"] for r in results_list]

    print(f"\n{'=' * 70}")
    print("LATENCY STATISTICS")
    print(f"{'=' * 70}")
    print(f"  Mean:   {np.mean(latencies):.0f} ms")
    print(f"  Median: {np.median(latencies):.0f} ms")
    print(f"  P95:    {np.percentile(latencies, 95):.0f} ms")
    print(f"  Max:    {np.max(latencies):.0f} ms")
    print(f"  Total:  {total_time / 1000:.1f}s for {len(test_data)} items")

    # ── Save results ─────────────────────────────────────────────────
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "timestamp": timestamp,
        "dataset_size": len(test_data),
        "coverage": {
            "items_with_results": len(items_with_results),
            "total": len(test_data),
            "rate": coverage_rate,
        },
        "emotion_classification": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "per_class_report": report,
            "confusion_matrix": {
                "labels": emotion_labels,
                "matrix": cm.tolist(),
            },
        },
        "hourglass_correlations": hourglass_correlations,
        "dimension_distributions": dimension_stats,
        "low_variance_dimensions": low_variance_flags,
        "latency_stats": {
            "mean_ms": float(np.mean(latencies)),
            "median_ms": float(np.median(latencies)),
            "p95_ms": float(np.percentile(latencies, 95)),
            "max_ms": float(np.max(latencies)),
            "total_s": total_time / 1000,
        },
        "error_analysis": {
            "total_errors": len(errors),
            "errors_by_expected": {
                k: len(v) for k, v in error_by_expected.items()
            },
        },
        "failed_analyses": failed_analyses,
        "all_results": results_list,
    }

    output_path = RESULTS_DIR / f"senticnet_accuracy_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    return output


if __name__ == "__main__":
    asyncio.run(run_evaluation())

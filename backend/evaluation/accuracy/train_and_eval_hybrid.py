"""
Approach A: Train and evaluate the Hybrid Emotion Classifier.

Step 1: Extract SenticNet features for all training + test sentences (cached to disk)
Step 2: Train Hybrid classifier (embedding + SenticNet features)
Step 3: Evaluate on 50-sentence test set
Step 4: Save results

Usage:
    python -m evaluation.accuracy.train_and_eval_hybrid
    python -m evaluation.accuracy.train_and_eval_hybrid --skip-senticnet  # use cached features
"""

import asyncio
import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

TRAIN_PATH = ROOT / "evaluation" / "data" / "emotion_training_data.json"
TEST_PATH = ROOT / "evaluation" / "data" / "emotion_test_sentences.json"
CACHE_DIR = ROOT / "evaluation" / "data" / "senticnet_cache"
RESULTS_DIR = ROOT / "evaluation" / "results"

EMOTION_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]

SENTICNET_FEATURE_KEYS = [
    "polarity_score", "intensity", "introspection", "temper",
    "attitude", "sensitivity", "engagement", "wellbeing",
]


async def extract_senticnet_features(sentences: list[str], cache_path: Path) -> list[dict]:
    """Run SenticNet pipeline on all sentences and cache results."""
    from services.senticnet_pipeline import SenticNetPipeline

    if cache_path.exists():
        print(f"  Loading cached SenticNet features from {cache_path}")
        with open(cache_path) as f:
            return json.load(f)

    print(f"  Extracting SenticNet features for {len(sentences)} sentences...")
    pipeline = SenticNetPipeline()
    features_list: list[dict] = []

    for i, sentence in enumerate(sentences):
        print(f"    [{i+1}/{len(sentences)}] {sentence[:60]}...", end="", flush=True)
        try:
            result = await pipeline.analyze(text=sentence, mode="full")
            features = {
                "polarity_score": result.emotion.polarity_score,
                "intensity": result.adhd_signals.intensity_score,
                "introspection": result.emotion.introspection,
                "temper": result.emotion.temper,
                "attitude": result.emotion.attitude,
                "sensitivity": result.emotion.sensitivity,
                "engagement": result.adhd_signals.engagement_score,
                "wellbeing": result.adhd_signals.wellbeing_score,
            }
            features_list.append(features)
            print(f" OK")
        except Exception as e:
            print(f" ERROR: {e}")
            features_list.append({k: 0.0 for k in SENTICNET_FEATURE_KEYS})

    await pipeline.close()

    # Cache to disk
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(features_list, f, indent=2)
    print(f"  Cached SenticNet features to {cache_path}")

    return features_list


def features_dict_to_array(features: dict) -> np.ndarray:
    """Convert feature dict to numpy array."""
    return np.array(
        [float(features.get(k, 0.0)) for k in SENTICNET_FEATURE_KEYS],
        dtype=np.float32,
    )


async def main(skip_senticnet: bool = False) -> dict:
    print("=" * 70)
    print("APPROACH A: HYBRID EMOTION CLASSIFIER (embedding + SenticNet features)")
    print("=" * 70)

    # ── Load data ─────────────────────────────────────────────────────
    with open(TRAIN_PATH) as f:
        train_data = json.load(f)
    with open(TEST_PATH) as f:
        test_data = json.load(f)

    train_sentences = [d["sentence"] for d in train_data]
    train_labels = [d["label"] for d in train_data]
    test_sentences = [d["sentence"] for d in test_data]
    test_labels = [d["expected_emotion"] for d in test_data]

    print(f"\nTraining: {len(train_sentences)} sentences")
    print(f"Test:     {len(test_sentences)} sentences")

    # ── Step 1: Extract SenticNet features ────────────────────────────
    print(f"\n{'─' * 70}")
    print("STEP 1: SenticNet Feature Extraction")
    print(f"{'─' * 70}")

    if skip_senticnet:
        print("  Using zero-vectors for SenticNet features (--skip-senticnet)")
        train_sn_features = [{k: 0.0 for k in SENTICNET_FEATURE_KEYS} for _ in train_sentences]
        test_sn_features = [{k: 0.0 for k in SENTICNET_FEATURE_KEYS} for _ in test_sentences]
    else:
        train_sn_features = await extract_senticnet_features(
            train_sentences,
            CACHE_DIR / "train_senticnet_features.json",
        )
        test_sn_features = await extract_senticnet_features(
            test_sentences,
            CACHE_DIR / "test_senticnet_features.json",
        )

    train_sn_arrays = [features_dict_to_array(f) for f in train_sn_features]
    test_sn_arrays = [features_dict_to_array(f) for f in test_sn_features]

    # ── Step 2: Train classifier ──────────────────────────────────────
    print(f"\n{'─' * 70}")
    print("STEP 2: Training Hybrid Classifier")
    print(f"{'─' * 70}")

    from services.emotion_classifier_hybrid import HybridEmotionClassifier

    # Train both variants
    results_all: dict[str, dict] = {}

    for classifier_type in ["logistic", "mlp"]:
        print(f"\n  Training {classifier_type.upper()} classifier...")
        classifier = HybridEmotionClassifier()
        train_start = time.perf_counter()
        train_metrics = classifier.train(
            texts=train_sentences,
            senticnet_features_list=train_sn_arrays,
            labels=train_labels,
            classifier_type=classifier_type,
        )
        train_time = time.perf_counter() - train_start
        print(f"    Training time: {train_time:.2f}s")
        print(f"    Training accuracy: {train_metrics['train_accuracy']:.4f}")

        # ── Step 3: Evaluate on test set ──────────────────────────────
        print(f"\n  Evaluating {classifier_type.upper()} on test set...")
        y_pred = []
        confidences = []
        eval_start = time.perf_counter()

        for text, sn_features in zip(test_sentences, test_sn_arrays):
            label, conf = classifier.predict(text, sn_features)
            y_pred.append(label)
            confidences.append(conf)

        eval_time = time.perf_counter() - eval_start

        accuracy = accuracy_score(test_labels, y_pred)
        macro_f1 = f1_score(test_labels, y_pred, labels=EMOTION_LABELS, average="macro", zero_division=0)
        weighted_f1 = f1_score(test_labels, y_pred, labels=EMOTION_LABELS, average="weighted", zero_division=0)
        cm = confusion_matrix(test_labels, y_pred, labels=EMOTION_LABELS)
        report = classification_report(
            test_labels, y_pred, labels=EMOTION_LABELS, output_dict=True, zero_division=0,
        )

        print(f"\n    {classifier_type.upper()} Results:")
        print(f"    Accuracy:    {accuracy:.4f} ({accuracy * 100:.1f}%)")
        print(f"    Macro-F1:    {macro_f1:.4f}")
        print(f"    Weighted-F1: {weighted_f1:.4f}")
        print(f"    Eval time:   {eval_time:.2f}s ({eval_time / len(test_sentences) * 1000:.1f}ms/sample)")
        print(f"    Avg confidence: {np.mean(confidences):.4f}")

        print(f"\n    Classification Report:")
        print(classification_report(test_labels, y_pred, labels=EMOTION_LABELS, zero_division=0))

        print("    Confusion Matrix:")
        header = f"    {'':>15s}" + "".join(f"  {l[:8]:>8s}" for l in EMOTION_LABELS)
        print(header)
        for i, label in enumerate(EMOTION_LABELS):
            row = cm[i].tolist()
            row_str = "".join(f"  {v:>8d}" for v in row)
            print(f"    {label:>15s}{row_str}")

        # Save model
        save_dir = classifier.save()
        print(f"\n    Model saved to: {save_dir}")

        # Error analysis
        errors = []
        for j in range(len(test_sentences)):
            if y_pred[j] != test_labels[j]:
                errors.append({
                    "sentence": test_sentences[j],
                    "expected": test_labels[j],
                    "predicted": y_pred[j],
                    "confidence": confidences[j],
                })

        results_all[classifier_type] = {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "per_class_report": report,
            "confusion_matrix": {"labels": EMOTION_LABELS, "matrix": cm.tolist()},
            "train_accuracy": train_metrics["train_accuracy"],
            "train_time_s": train_time,
            "eval_time_s": eval_time,
            "avg_confidence": float(np.mean(confidences)),
            "n_errors": len(errors),
            "errors": errors,
        }

    # ── Save results ──────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "approach": "A_hybrid",
        "timestamp": timestamp,
        "train_size": len(train_sentences),
        "test_size": len(test_sentences),
        "skip_senticnet": skip_senticnet,
        "results": results_all,
    }

    output_path = RESULTS_DIR / f"approach_a_hybrid_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 70}")
    print("APPROACH A SUMMARY")
    print(f"{'=' * 70}")
    for ctype, res in results_all.items():
        print(f"  {ctype.upper():>10s}: accuracy={res['accuracy']:.4f}, macro-F1={res['macro_f1']:.4f}, errors={res['n_errors']}")
    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-senticnet", action="store_true",
                        help="Skip SenticNet API calls, use zero features (embedding-only baseline)")
    args = parser.parse_args()
    asyncio.run(main(skip_senticnet=args.skip_senticnet))

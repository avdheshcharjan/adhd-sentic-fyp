"""
Approach C (Augmented): Train DistilBERT on massive multi-source emotion dataset.

Uses 30,000 balanced samples (5,000 per class) collected from:
    - dair-ai/emotion (416K)
    - GoEmotions (30K)
    - Empathetic Dialogues (73K)
    - SuperEmotion (413K)
    - DailyDialog (14K)
    - Our 210 ADHD base sentences

All mapped to our 6 ADHD categories:
    joyful, focused, frustrated, anxious, disengaged, overwhelmed

Usage:
    python -m evaluation.accuracy.train_and_eval_finetune_augmented
    python -m evaluation.accuracy.train_and_eval_finetune_augmented --epochs 10
"""

import argparse
import json
import sys
import time
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

AUGMENTED_DATA_PATH = ROOT / "evaluation" / "data" / "augmented_emotion_training_data.json"
TEST_PATH = ROOT / "evaluation" / "data" / "emotion_test_sentences.json"
RESULTS_DIR = ROOT / "evaluation" / "results"

EMOTION_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]


def main(num_epochs: int = 10, batch_size: int = 32, learning_rate: float = 2e-5) -> dict:
    print("=" * 70)
    print("APPROACH C (AUGMENTED): DISTILBERT ON MASSIVE MULTI-SOURCE DATASET")
    print("=" * 70)

    # ── Load data ─────────────────────────────────────────────────────
    if not AUGMENTED_DATA_PATH.exists():
        print(f"\n  ⚠ Augmented data not found at {AUGMENTED_DATA_PATH}")
        print("  Run first: python -m evaluation.data.collect_emotion_datasets")
        sys.exit(1)

    with open(AUGMENTED_DATA_PATH) as f:
        train_data = json.load(f)
    with open(TEST_PATH) as f:
        test_data = json.load(f)

    train_sentences = [d["sentence"] for d in train_data]
    train_labels = [d["label"] for d in train_data]
    test_sentences = [d["sentence"] for d in test_data]
    test_labels = [d["expected_emotion"] for d in test_data]

    from collections import Counter
    train_dist = Counter(train_labels)
    print(f"\nTraining: {len(train_sentences)} sentences")
    print(f"  Distribution: {dict(sorted(train_dist.items()))}")
    print(f"Test:     {len(test_sentences)} sentences")

    # ── Train DistilBERT ──────────────────────────────────────────────
    from services.emotion_classifier_finetune import FineTuneEmotionClassifier

    results_all: dict[str, dict] = {}

    config_name = f"distilbert_{num_epochs}ep_aug30k"
    config = {
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
    }

    print(f"\n{'─' * 70}")
    print(f"Config: {config_name} ({config})")
    print(f"{'─' * 70}")

    classifier = FineTuneEmotionClassifier(model_name="distilbert-base-uncased")

    train_start = time.perf_counter()
    train_metrics = classifier.train(
        texts=train_sentences,
        labels=train_labels,
        **config,
    )
    train_time = time.perf_counter() - train_start
    print(f"\n  Training time: {train_time:.2f}s")
    print(f"  Training accuracy: {train_metrics['train_accuracy']:.4f}")

    # ── Evaluate on test set ──────────────────────────────────────
    print(f"\n  Evaluating on test set...")
    y_pred = []
    confidences = []
    eval_start = time.perf_counter()

    for text in test_sentences:
        label, conf = classifier.predict(text)
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

    print(f"\n  {config_name.upper()} Results:")
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

    results_all[config_name] = {
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
        "config": config,
        "augmented": True,
        "train_size": len(train_sentences),
    }

    # ── Save results ──────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "approach": "C_finetune_augmented",
        "timestamp": timestamp,
        "train_size": len(train_sentences),
        "test_size": len(test_sentences),
        "data_sources": [
            "dair-ai/emotion (416K)",
            "GoEmotions (30K)",
            "Empathetic Dialogues (73K)",
            "SuperEmotion (413K)",
            "DailyDialog (14K)",
            "ADHD base (210)",
        ],
        "results": results_all,
    }

    output_path = RESULTS_DIR / f"approach_c_finetune_augmented_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 70}")
    print("APPROACH C (AUGMENTED) SUMMARY")
    print(f"{'=' * 70}")
    for cname, res in results_all.items():
        print(f"  {cname:>30s}: accuracy={res['accuracy']:.4f}, macro-F1={res['macro_f1']:.4f}, errors={res['n_errors']}")
    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    args = parser.parse_args()
    main(num_epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)

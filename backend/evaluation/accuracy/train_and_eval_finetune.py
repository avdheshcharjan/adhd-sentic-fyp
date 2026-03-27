"""
Approach C: Train and evaluate the Fine-Tuned Transformer Emotion Classifier.

Trains DistilBERT on our ADHD training data (210 sentences) plus optionally
augmented data from the HuggingFace emotion dataset (mapped to our 6 categories).

Usage:
    python -m evaluation.accuracy.train_and_eval_finetune
    python -m evaluation.accuracy.train_and_eval_finetune --augment  # add external data
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

TRAIN_PATH = ROOT / "evaluation" / "data" / "emotion_training_data.json"
TEST_PATH = ROOT / "evaluation" / "data" / "emotion_test_sentences.json"
RESULTS_DIR = ROOT / "evaluation" / "results"

EMOTION_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]


def load_augmented_data() -> tuple[list[str], list[str]]:
    """Load and map external emotion dataset to our 6 ADHD categories.

    Uses the HuggingFace 'dair-ai/emotion' dataset which has 6 classes:
        sadness(0), joy(1), love(2), anger(3), fear(4), surprise(5)
    Mapped to our categories:
        sadness → overwhelmed, joy → joyful, love → joyful,
        anger → frustrated, fear → anxious, surprise → focused
    """
    from datasets import load_dataset

    print("  Loading HuggingFace 'dair-ai/emotion' dataset...")
    dataset = load_dataset("dair-ai/emotion", split="train")

    hf_label_map = {
        0: "overwhelmed",  # sadness
        1: "joyful",       # joy
        2: "joyful",       # love
        3: "frustrated",   # anger
        4: "anxious",      # fear
        5: "focused",      # surprise
    }

    texts = []
    labels = []

    # Sample a balanced subset (max 200 per mapped class to avoid imbalance)
    from collections import Counter
    class_counts: Counter = Counter()
    max_per_class = 200

    for item in dataset:
        mapped_label = hf_label_map[item["label"]]
        if class_counts[mapped_label] < max_per_class:
            texts.append(item["text"])
            labels.append(mapped_label)
            class_counts[mapped_label] += 1

    # Note: 'disengaged' has no direct mapping in this dataset
    # It only appears from our ADHD training data
    print(f"  Loaded {len(texts)} external samples: {dict(class_counts)}")
    return texts, labels


def main(augment: bool = False) -> dict:
    print("=" * 70)
    print("APPROACH C: FINE-TUNED TRANSFORMER EMOTION CLASSIFIER")
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

    print(f"\nBase training: {len(train_sentences)} ADHD sentences")

    # Optionally augment with external data
    if augment:
        print(f"\n{'─' * 70}")
        print("Loading augmented data from HuggingFace emotion dataset")
        print(f"{'─' * 70}")
        aug_texts, aug_labels = load_augmented_data()
        train_sentences = train_sentences + aug_texts
        train_labels = train_labels + aug_labels
        print(f"Combined training: {len(train_sentences)} sentences")

    print(f"Test:     {len(test_sentences)} sentences")

    # ── Train DistilBERT ──────────────────────────────────────────────
    from services.emotion_classifier_finetune import FineTuneEmotionClassifier

    results_all: dict[str, dict] = {}

    configs = [
        ("distilbert_5ep", {"num_epochs": 5, "batch_size": 16, "learning_rate": 2e-5}),
        ("distilbert_10ep", {"num_epochs": 10, "batch_size": 16, "learning_rate": 2e-5}),
    ]

    for config_name, config in configs:
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
            "augmented": augment,
        }

    # ── Save results ──────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "approach": "C_finetune",
        "timestamp": timestamp,
        "train_size": len(train_sentences),
        "test_size": len(test_sentences),
        "augmented": augment,
        "results": results_all,
    }

    output_path = RESULTS_DIR / f"approach_c_finetune_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 70}")
    print("APPROACH C SUMMARY")
    print(f"{'=' * 70}")
    for cname, res in results_all.items():
        print(f"  {cname:>20s}: accuracy={res['accuracy']:.4f}, macro-F1={res['macro_f1']:.4f}, errors={res['n_errors']}")
    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--augment", action="store_true",
                        help="Augment training data with HuggingFace emotion dataset")
    args = parser.parse_args()
    main(augment=args.augment)

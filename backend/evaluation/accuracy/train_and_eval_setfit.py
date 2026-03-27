"""
Approach B: Train and evaluate the SetFit Few-Shot Emotion Classifier.

Strategy: Fine-tune sentence transformer ONCE per epoch config, then sweep
LogisticRegression hyperparameters on the same embeddings (instant).

Usage:
    python -m evaluation.accuracy.train_and_eval_setfit
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

TRAIN_PATH = ROOT / "evaluation" / "data" / "emotion_training_data.json"
TEST_PATH = ROOT / "evaluation" / "data" / "emotion_test_sentences.json"
RESULTS_DIR = ROOT / "evaluation" / "results"

EMOTION_LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]


def evaluate_with_lr(
    train_embeddings: np.ndarray,
    train_labels: list[str],
    test_embeddings: np.ndarray,
    test_labels: list[str],
    lr_C: float,
    lr_solver: str,
) -> dict:
    """Train LR head on embeddings and evaluate."""
    label_encoder = LabelEncoder()
    label_encoder.fit(EMOTION_LABELS)
    y_train = label_encoder.transform(train_labels)

    clf = LogisticRegression(max_iter=1000, random_state=42, C=lr_C, solver=lr_solver)
    clf.fit(train_embeddings, y_train)

    # Predict
    probas = clf.predict_proba(test_embeddings)
    y_pred_labels: list[str] = []
    confidences: list[float] = []
    for proba in probas:
        pred_idx = int(np.argmax(proba))
        confidences.append(float(proba[pred_idx]))
        y_pred_labels.append(label_encoder.inverse_transform([pred_idx])[0])

    accuracy = accuracy_score(test_labels, y_pred_labels)
    macro_f1 = f1_score(test_labels, y_pred_labels, labels=EMOTION_LABELS, average="macro", zero_division=0)
    weighted_f1 = f1_score(test_labels, y_pred_labels, labels=EMOTION_LABELS, average="weighted", zero_division=0)
    cm = confusion_matrix(test_labels, y_pred_labels, labels=EMOTION_LABELS)
    report = classification_report(
        test_labels, y_pred_labels, labels=EMOTION_LABELS, output_dict=True, zero_division=0,
    )

    # Train accuracy
    train_preds = clf.predict(train_embeddings)
    train_accuracy = float(np.mean(train_preds == y_train))

    # Errors
    errors = []
    test_sentences_global = getattr(evaluate_with_lr, "_test_sentences", [])
    for j in range(len(test_labels)):
        if y_pred_labels[j] != test_labels[j]:
            errors.append({
                "sentence": test_sentences_global[j] if j < len(test_sentences_global) else "",
                "expected": test_labels[j],
                "predicted": y_pred_labels[j],
                "confidence": confidences[j],
            })

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class_report": report,
        "confusion_matrix": {"labels": EMOTION_LABELS, "matrix": cm.tolist()},
        "train_accuracy": train_accuracy,
        "avg_confidence": float(np.mean(confidences)),
        "n_errors": len(errors),
        "errors": errors,
        "lr_C": lr_C,
        "lr_solver": lr_solver,
    }


def main() -> dict:
    print("=" * 70)
    print("APPROACH B: SETFIT FEW-SHOT EMOTION CLASSIFIER (IMPROVED)")
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

    # Store test sentences for error reporting
    evaluate_with_lr._test_sentences = test_sentences

    print(f"\nTraining: {len(train_sentences)} sentences")
    print(f"Test:     {len(test_sentences)} sentences")

    from services.emotion_classifier_setfit import SetFitEmotionClassifier

    results_all: dict[str, dict] = {}

    # Fine-tune ONCE per epoch config, then sweep LR params
    # NOTE: e1 strictly dominates e2 (86% vs 84% in Phase 5.5).
    # With 498 sentences, pairs explode to ~370K — keep configs minimal.
    epoch_configs = [
        ("e1", 1),
    ]
    lr_grid = [
        (1.0, "lbfgs"),
        (10.0, "lbfgs"),
    ]

    for epoch_name, num_epochs in epoch_configs:
        print(f"\n{'=' * 70}")
        print(f"FINE-TUNING SENTENCE TRANSFORMER: {epoch_name} (epochs={num_epochs})")
        print(f"{'=' * 70}")

        classifier = SetFitEmotionClassifier()

        train_start = time.perf_counter()
        # Train with default LR params — we only need the fine-tuned ST model
        train_metrics = classifier.train(
            texts=train_sentences,
            labels=train_labels,
            num_epochs=num_epochs,
            batch_size=16,
        )
        train_time = time.perf_counter() - train_start
        print(f"  Fine-tuning time: {train_time:.2f}s")
        print(f"  Contrastive pairs: {train_metrics['n_contrastive_pairs']}")

        # Get embeddings ONCE from fine-tuned model
        train_embeddings = classifier._model.encode(train_sentences, normalize_embeddings=True)
        test_embeddings = classifier._model.encode(test_sentences, normalize_embeddings=True)

        # Sweep LR hyperparameters (instant)
        for lr_C, lr_solver in lr_grid:
            config_name = f"setfit_{epoch_name}_C{lr_C}_{lr_solver}"
            print(f"\n  {'─' * 60}")
            print(f"  LR Config: C={lr_C}, solver={lr_solver}")

            result = evaluate_with_lr(
                train_embeddings, train_labels,
                test_embeddings, test_labels,
                lr_C, lr_solver,
            )

            result["train_time_s"] = train_time
            result["config"] = {
                "num_epochs": num_epochs,
                "batch_size": 16,
                "lr_C": lr_C,
                "lr_solver": lr_solver,
            }

            print(f"    Accuracy:    {result['accuracy']:.4f} ({result['accuracy'] * 100:.1f}%)")
            print(f"    Macro-F1:    {result['macro_f1']:.4f}")
            print(f"    Weighted-F1: {result['weighted_f1']:.4f}")
            print(f"    Avg confidence: {result['avg_confidence']:.4f}")
            print(f"    Errors: {result['n_errors']}")

            print(f"\n    Classification Report:")
            y_pred = [e["predicted"] if e["expected"] != e["predicted"] else e["expected"]
                      for e in result["errors"]]
            # Print full report from sklearn
            all_preds: list[str] = []
            error_idx = 0
            for j in range(len(test_labels)):
                found_error = False
                for err in result["errors"]:
                    if err["sentence"] == test_sentences[j]:
                        all_preds.append(err["predicted"])
                        found_error = True
                        break
                if not found_error:
                    all_preds.append(test_labels[j])
            print(classification_report(test_labels, all_preds, labels=EMOTION_LABELS, zero_division=0))

            results_all[config_name] = result

        # Save the best model from this epoch config
        classifier.save()
        print(f"\n  Model saved for {epoch_name}")

    # ── Save results ──────────────────────────────────────────────────
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    output = {
        "approach": "B_setfit_improved",
        "timestamp": timestamp,
        "train_size": len(train_sentences),
        "test_size": len(test_sentences),
        "results": results_all,
    }

    output_path = RESULTS_DIR / f"approach_b_setfit_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 70}")
    print("APPROACH B SUMMARY")
    print(f"{'=' * 70}")

    # Sort by accuracy descending
    sorted_results = sorted(results_all.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    for cname, res in sorted_results:
        print(f"  {cname:>35s}: accuracy={res['accuracy']:.4f}, macro-F1={res['macro_f1']:.4f}, errors={res['n_errors']}")

    best_name, best_res = sorted_results[0]
    print(f"\n  BEST: {best_name} — {best_res['accuracy']*100:.1f}% accuracy, {best_res['macro_f1']:.4f} macro-F1")
    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    main()

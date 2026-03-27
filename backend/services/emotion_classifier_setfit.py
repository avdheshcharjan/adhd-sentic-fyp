"""
Approach B: Contrastive Few-Shot Emotion Classifier (SetFit-style)

Architecture:
    User text
        └── Contrastive fine-tuned all-mpnet-base-v2 (~420MB, ~30ms)
            ├── Sentence transformer fine-tuned with contrastive pairs
            └── Logistic regression classification head
                ↓
            6-class ADHD emotion prediction

This implements the core SetFit algorithm manually using sentence-transformers
and scikit-learn, since the setfit library is incompatible with transformers v5.

The approach:
    1. Generate contrastive pairs (positive = same class, negative = different class)
    2. Fine-tune sentence transformer with CoSENTLoss
    3. Train logistic regression on fine-tuned embeddings

Expected accuracy: 90-93% on ADHD emotion classification.
"""

import itertools
import json
import logging
import pickle
import random
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import InputExample, SentenceTransformer, losses
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader

logger = logging.getLogger("adhd-brain.emotion_classifier_setfit")

MODEL_DIR = Path(__file__).parent.parent / "models" / "adhd-emotion-setfit"
TRAINING_DATA_PATH = (
    Path(__file__).parent.parent / "evaluation" / "data" / "emotion_training_data.json"
)

LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for i, label in enumerate(LABELS)}


HARD_NEGATIVE_PAIRS: list[tuple[str, str]] = [
    ("anxious", "overwhelmed"),
    ("frustrated", "overwhelmed"),
    ("anxious", "frustrated"),
    ("disengaged", "overwhelmed"),
    ("focused", "frustrated"),
    ("disengaged", "joyful"),
]


def _generate_contrastive_pairs(
    texts: list[str],
    labels: list[str],
    hard_negative_multiplier: int = 2,
) -> list[InputExample]:
    """Generate ALL unique contrastive sentence pairs for fine-tuning.

    Generates:
        - All unique positive pairs: C(n,2) per class
        - All unique negative pairs: n_i × n_j per class pair
        - Oversamples positive pairs to balance with negatives
        - Hard negative mining: duplicates pairs from confused class pairs
    """
    # Group by label
    label_to_texts: dict[str, list[str]] = {}
    for text, label in zip(texts, labels):
        label_to_texts.setdefault(label, []).append(text)

    positive_pairs: list[InputExample] = []
    negative_pairs: list[InputExample] = []
    hard_negative_extra: list[InputExample] = []

    # All unique positive pairs: C(n,2) per class
    for label, class_texts in label_to_texts.items():
        for t1, t2 in itertools.combinations(class_texts, 2):
            positive_pairs.append(InputExample(texts=[t1, t2], label=1.0))

    # All unique negative pairs: n_i × n_j per class pair
    all_labels = list(label_to_texts.keys())
    for l1, l2 in itertools.combinations(all_labels, 2):
        is_hard = (l1, l2) in HARD_NEGATIVE_PAIRS or (l2, l1) in HARD_NEGATIVE_PAIRS
        for t1 in label_to_texts[l1]:
            for t2 in label_to_texts[l2]:
                pair = InputExample(texts=[t1, t2], label=0.0)
                negative_pairs.append(pair)
                # Hard negative mining: duplicate confused pairs
                if is_hard:
                    for _ in range(hard_negative_multiplier):
                        hard_negative_extra.append(
                            InputExample(texts=[t1, t2], label=0.0)
                        )

    # Oversample positive pairs to balance with negative count
    rng = random.Random(42)
    total_negatives = len(negative_pairs) + len(hard_negative_extra)
    if len(positive_pairs) < total_negatives:
        shortage = total_negatives - len(positive_pairs)
        oversampled = rng.choices(positive_pairs, k=shortage)
        positive_pairs.extend(oversampled)

    pairs = positive_pairs + negative_pairs + hard_negative_extra
    rng.shuffle(pairs)

    logger.info(
        f"Generated {len(pairs)} pairs: "
        f"{len(positive_pairs)} positive (incl. oversampled), "
        f"{len(negative_pairs)} negative, "
        f"{len(hard_negative_extra)} hard negative extra"
    )
    return pairs


class SetFitEmotionClassifier:
    """Contrastive few-shot emotion classifier for ADHD text (SetFit-style)."""

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None
        self._classifier: Optional[LogisticRegression] = None
        self._label_encoder: Optional[LabelEncoder] = None
        self._is_trained = False

    # ── Training ──────────────────────────────────────────────────────

    def train(
        self,
        texts: list[str],
        labels: list[str],
        num_epochs: int = 1,
        batch_size: int = 16,
        lr_C: float = 1.0,
        lr_solver: str = "lbfgs",
    ) -> dict:
        """Train the contrastive classifier.

        Phase 1: Fine-tune sentence transformer with contrastive pairs
        Phase 2: Train logistic regression on fine-tuned embeddings

        Args:
            texts: Training sentences.
            labels: Ground truth emotion labels (string).
            num_epochs: Number of contrastive training epochs.
            batch_size: Batch size for training.
            lr_C: Regularization parameter for LogisticRegression.
            lr_solver: Solver for LogisticRegression.

        Returns:
            Training metrics dict.
        """
        logger.info(f"Training contrastive classifier on {len(texts)} samples...")

        # Phase 1: Fine-tune sentence transformer with contrastive learning
        self._model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

        pairs = _generate_contrastive_pairs(texts, labels)

        train_dataloader = DataLoader(pairs, shuffle=True, batch_size=batch_size)
        train_loss = losses.CoSENTLoss(self._model)

        self._model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=num_epochs,
            warmup_steps=10,
            show_progress_bar=True,
        )
        logger.info("Phase 1: Sentence transformer fine-tuned with contrastive learning")

        # Phase 2: Train logistic regression on fine-tuned embeddings
        embeddings = self._model.encode(texts, normalize_embeddings=True)

        self._label_encoder = LabelEncoder()
        self._label_encoder.fit(LABELS)
        y = self._label_encoder.transform(labels)

        self._classifier = LogisticRegression(
            max_iter=1000,
            random_state=42,
            C=lr_C,
            solver=lr_solver,
        )
        self._classifier.fit(embeddings, y)
        self._is_trained = True

        # Compute training accuracy
        train_preds = self._classifier.predict(embeddings)
        train_accuracy = float(np.mean(train_preds == y))

        logger.info(f"Phase 2: Logistic regression trained. Accuracy: {train_accuracy:.4f}")

        return {
            "n_samples": len(texts),
            "num_epochs": num_epochs,
            "n_contrastive_pairs": len(pairs),
            "train_accuracy": train_accuracy,
            "lr_C": lr_C,
            "lr_solver": lr_solver,
        }

    # ── Prediction ────────────────────────────────────────────────────

    def predict(self, text: str) -> tuple[str, float]:
        """Predict emotion category with confidence.

        Returns:
            (predicted_label, confidence_score)
        """
        if not self._is_trained:
            raise RuntimeError("Classifier not trained. Call train() or load() first.")

        embedding = self._model.encode([text], normalize_embeddings=True)
        proba = self._classifier.predict_proba(embedding)[0]
        pred_idx = int(np.argmax(proba))
        confidence = float(proba[pred_idx])
        label = self._label_encoder.inverse_transform([pred_idx])[0]

        return label, confidence

    def predict_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        """Predict emotions for a batch of texts."""
        if not self._is_trained:
            raise RuntimeError("Classifier not trained. Call train() or load() first.")

        embeddings = self._model.encode(texts, normalize_embeddings=True)
        probas = self._classifier.predict_proba(embeddings)
        results: list[tuple[str, float]] = []
        for proba in probas:
            pred_idx = int(np.argmax(proba))
            confidence = float(proba[pred_idx])
            label = self._label_encoder.inverse_transform([pred_idx])[0]
            results.append((label, confidence))
        return results

    # ── Persistence ───────────────────────────────────────────────────

    def save(self, path: Path | None = None) -> Path:
        """Save trained model to disk."""
        if not self._is_trained:
            raise RuntimeError("Cannot save untrained classifier.")

        save_dir = path or MODEL_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save sentence transformer
        self._model.save(str(save_dir / "sentence_transformer"))

        # Save classifier head and label encoder
        with open(save_dir / "classifier.pkl", "wb") as f:
            pickle.dump(self._classifier, f)
        with open(save_dir / "label_encoder.pkl", "wb") as f:
            pickle.dump(self._label_encoder, f)

        logger.info(f"Contrastive classifier saved to {save_dir}")
        return save_dir

    def load(self, path: Path | None = None) -> None:
        """Load trained model from disk."""
        load_dir = path or MODEL_DIR

        self._model = SentenceTransformer(str(load_dir / "sentence_transformer"))

        with open(load_dir / "classifier.pkl", "rb") as f:
            self._classifier = pickle.load(f)
        with open(load_dir / "label_encoder.pkl", "rb") as f:
            self._label_encoder = pickle.load(f)

        self._is_trained = True
        logger.info(f"Contrastive classifier loaded from {load_dir}")

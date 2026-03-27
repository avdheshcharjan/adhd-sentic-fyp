"""
Approach A: Hybrid Emotion Classifier

Architecture:
    User text
        ├── all-MiniLM-L6-v2 → 384-dim sentence embedding
        ├── SenticNet API → 8 numeric features (polarity_score, intensity,
        │   introspection, temper, attitude, sensitivity, engagement, wellbeing)
        └── Combine: [384-dim] + [8 features] = 392-dim
              ↓
            Logistic Regression / MLP classifier
              ↓
            6-class ADHD emotion prediction

Expected accuracy: 88-94% on ADHD emotion classification.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger("adhd-brain.emotion_classifier_hybrid")

MODEL_DIR = Path(__file__).parent.parent / "models" / "adhd-emotion-hybrid"
TRAINING_DATA_PATH = (
    Path(__file__).parent.parent / "evaluation" / "data" / "emotion_training_data.json"
)

LABELS = ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]


class HybridEmotionClassifier:
    """Hybrid classifier combining sentence embeddings with SenticNet features."""

    def __init__(self) -> None:
        self._embedding_model: Optional[SentenceTransformer] = None
        self._classifier: Optional[LogisticRegression | MLPClassifier] = None
        self._scaler: Optional[StandardScaler] = None
        self._label_encoder: Optional[LabelEncoder] = None
        self._is_trained = False

    # ── Lazy model loading ────────────────────────────────────────────

    def _ensure_embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded all-MiniLM-L6-v2 for hybrid classifier")
        return self._embedding_model

    # ── Feature extraction ────────────────────────────────────────────

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get 384-dim sentence embedding."""
        model = self._ensure_embedding_model()
        embedding: np.ndarray = model.encode(text, normalize_embeddings=True)
        return embedding

    @staticmethod
    def _extract_senticnet_features(senticnet_result: dict) -> np.ndarray:
        """Extract 8 numeric features from a SenticNet pipeline result.

        Expected keys:
            polarity_score, intensity, introspection, temper,
            attitude, sensitivity, engagement, wellbeing
        All values are floats, typically in [-100, 100] range.
        """
        feature_keys = [
            "polarity_score", "intensity", "introspection", "temper",
            "attitude", "sensitivity", "engagement", "wellbeing",
        ]
        features = np.array(
            [float(senticnet_result.get(k, 0.0)) for k in feature_keys],
            dtype=np.float32,
        )
        return features

    def _build_feature_vector(
        self, text: str, senticnet_features: np.ndarray
    ) -> np.ndarray:
        """Combine embedding + SenticNet features into 392-dim vector."""
        embedding = self._get_embedding(text)  # (384,)
        combined = np.concatenate([embedding, senticnet_features])  # (392,)
        return combined

    # ── Training ──────────────────────────────────────────────────────

    def train(
        self,
        texts: list[str],
        senticnet_features_list: list[np.ndarray],
        labels: list[str],
        classifier_type: str = "mlp",
    ) -> dict:
        """Train the hybrid classifier.

        Args:
            texts: Training sentences.
            senticnet_features_list: 8-dim SenticNet feature vectors per sentence.
            labels: Ground truth emotion labels.
            classifier_type: "logistic" or "mlp".

        Returns:
            Training metrics dict.
        """
        logger.info(f"Training hybrid classifier ({classifier_type}) on {len(texts)} samples...")

        # Build feature matrix
        X_list = []
        for text, sn_features in zip(texts, senticnet_features_list):
            combined = self._build_feature_vector(text, sn_features)
            X_list.append(combined)
        X = np.array(X_list)

        # Encode labels
        self._label_encoder = LabelEncoder()
        self._label_encoder.fit(LABELS)
        y = self._label_encoder.transform(labels)

        # Scale features (important for SenticNet features which have different range than embeddings)
        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        # Train classifier
        if classifier_type == "mlp":
            self._classifier = MLPClassifier(
                hidden_layer_sizes=(256, 128),
                activation="relu",
                max_iter=500,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.15,
                learning_rate="adaptive",
            )
        else:
            self._classifier = LogisticRegression(
                max_iter=1000,
                multi_class="multinomial",
                random_state=42,
                C=1.0,
            )

        self._classifier.fit(X_scaled, y)
        self._is_trained = True

        # Compute training accuracy
        train_preds = self._classifier.predict(X_scaled)
        train_accuracy = float(np.mean(train_preds == y))

        logger.info(f"Hybrid classifier trained. Training accuracy: {train_accuracy:.4f}")

        return {
            "classifier_type": classifier_type,
            "n_samples": len(texts),
            "n_features": X.shape[1],
            "train_accuracy": train_accuracy,
        }

    # ── Prediction ────────────────────────────────────────────────────

    def predict(
        self, text: str, senticnet_features: np.ndarray
    ) -> tuple[str, float]:
        """Predict emotion category with confidence.

        Returns:
            (predicted_label, confidence_score)
        """
        if not self._is_trained:
            raise RuntimeError("Hybrid classifier not trained. Call train() or load() first.")

        combined = self._build_feature_vector(text, senticnet_features)
        X = self._scaler.transform(combined.reshape(1, -1))

        proba = self._classifier.predict_proba(X)[0]
        pred_idx = int(np.argmax(proba))
        confidence = float(proba[pred_idx])
        label = self._label_encoder.inverse_transform([pred_idx])[0]

        return label, confidence

    def predict_batch(
        self, texts: list[str], senticnet_features_list: list[np.ndarray]
    ) -> list[tuple[str, float]]:
        """Predict emotions for a batch of texts."""
        if not self._is_trained:
            raise RuntimeError("Hybrid classifier not trained. Call train() or load() first.")

        X_list = []
        for text, sn_features in zip(texts, senticnet_features_list):
            combined = self._build_feature_vector(text, sn_features)
            X_list.append(combined)
        X = np.array(X_list)
        X_scaled = self._scaler.transform(X)

        probas = self._classifier.predict_proba(X_scaled)
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

        with open(save_dir / "classifier.pkl", "wb") as f:
            pickle.dump(self._classifier, f)
        with open(save_dir / "scaler.pkl", "wb") as f:
            pickle.dump(self._scaler, f)
        with open(save_dir / "label_encoder.pkl", "wb") as f:
            pickle.dump(self._label_encoder, f)

        logger.info(f"Hybrid classifier saved to {save_dir}")
        return save_dir

    def load(self, path: Path | None = None) -> None:
        """Load trained model from disk."""
        load_dir = path or MODEL_DIR

        with open(load_dir / "classifier.pkl", "rb") as f:
            self._classifier = pickle.load(f)
        with open(load_dir / "scaler.pkl", "rb") as f:
            self._scaler = pickle.load(f)
        with open(load_dir / "label_encoder.pkl", "rb") as f:
            self._label_encoder = pickle.load(f)

        self._is_trained = True
        logger.info(f"Hybrid classifier loaded from {load_dir}")

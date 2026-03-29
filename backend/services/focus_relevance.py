"""
Focus relevance checker — determines if current screen activity is relevant
to the user's active focus task using embedding similarity.

Reuses the all-MiniLM-L6-v2 model already loaded by ActivityClassifier
(via shared_state.classifier) to avoid loading a second copy.
"""

import logging
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("adhd-brain.focus-relevance")

# Categories that are always considered on-task (system utilities, productivity tools)
ALWAYS_RELEVANT_CATEGORIES = {"system", "productivity"}

# Categories with stricter threshold — high suspicion of off-task behavior
HIGH_SUSPICION_CATEGORIES = {"entertainment", "social_media", "shopping", "news"}

DEFAULT_THRESHOLD = 0.20
HIGH_SUSPICION_THRESHOLD = 0.35


class FocusRelevanceChecker:
    """Checks whether current screen activity is relevant to the active focus task."""

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None
        self._cached_task_name: Optional[str] = None
        self._cached_task_embedding: Optional[np.ndarray] = None

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is None:
            # Try to reuse the model already loaded by ActivityClassifier
            from services.shared_state import classifier
            if classifier._embedding_model is not None:
                self._model = classifier._embedding_model
                logger.info("Reusing all-MiniLM-L6-v2 from ActivityClassifier")
            else:
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded all-MiniLM-L6-v2 for focus relevance")
        return self._model

    def _get_task_embedding(self, task_name: str) -> np.ndarray:
        """Get task embedding, using cache if task name hasn't changed."""
        if self._cached_task_name == task_name and self._cached_task_embedding is not None:
            return self._cached_task_embedding

        model = self._ensure_model()
        self._cached_task_embedding = model.encode(task_name, normalize_embeddings=True)
        self._cached_task_name = task_name
        logger.debug(f"Cached task embedding for: {task_name}")
        return self._cached_task_embedding

    def check_relevance(
        self,
        task_name: str,
        app_name: str,
        window_title: str,
        url: str | None,
        category: str,
        is_idle: bool,
    ) -> dict:
        """
        Check if the current activity is relevant to the focus task.

        Returns:
            {
                "off_task": bool,
                "similarity": float,
                "threshold": float,
                "reason": str
            }
        """
        # Never flag idle — user stepped away
        if is_idle:
            return {
                "off_task": False,
                "similarity": 1.0,
                "threshold": 0.0,
                "reason": "idle_bypass",
            }

        # Always-relevant categories bypass similarity check
        if category in ALWAYS_RELEVANT_CATEGORIES:
            return {
                "off_task": False,
                "similarity": 1.0,
                "threshold": 0.0,
                "reason": "always_relevant_category",
            }

        # Build activity text from available context
        parts = [app_name]
        if window_title:
            parts.append(window_title)
        if url:
            parts.append(url)
        activity_text = " - ".join(parts)

        # Compute similarity
        model = self._ensure_model()
        task_emb = self._get_task_embedding(task_name)
        activity_emb = model.encode(activity_text, normalize_embeddings=True)
        similarity = float(np.dot(task_emb, activity_emb))

        # Select threshold based on category suspicion level
        threshold = HIGH_SUSPICION_THRESHOLD if category in HIGH_SUSPICION_CATEGORIES else DEFAULT_THRESHOLD

        off_task = similarity < threshold
        reason = "below_threshold" if off_task else "relevant"

        return {
            "off_task": off_task,
            "similarity": round(similarity, 4),
            "threshold": threshold,
            "reason": reason,
        }

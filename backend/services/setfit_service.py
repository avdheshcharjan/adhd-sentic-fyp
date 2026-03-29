"""
SetFit emotion classifier singleton for production inference.

Loads the trained contrastive model once at import (~2-3s) and exposes
a module-level `setfit_classifier` instance used by senticnet_pipeline.py.
"""

import logging

from services.emotion_classifier_setfit import SetFitEmotionClassifier

logger = logging.getLogger("adhd-brain.setfit_service")

# SetFit label → ADHD state mapping
SETFIT_TO_ADHD_STATE: dict[str, str] = {
    "joyful": "productive_flow",
    "focused": "productive_flow",
    "frustrated": "frustration_spiral",
    "anxious": "anxiety_comorbid",
    "disengaged": "boredom_disengagement",
    "overwhelmed": "emotional_dysregulation",
}

# SetFit label → canonical PASE radar profile (0-1 scale).
# Each profile represents the typical emotional geometry of an ADHD state
# on the 4 radar axes used by the Swift dashboard.
SETFIT_TO_PASE: dict[str, dict[str, float]] = {
    "joyful":      {"pleasantness": 0.85, "attention": 0.70, "sensitivity": 0.30, "aptitude": 0.75},
    "focused":     {"pleasantness": 0.60, "attention": 0.90, "sensitivity": 0.20, "aptitude": 0.80},
    "frustrated":  {"pleasantness": 0.15, "attention": 0.40, "sensitivity": 0.80, "aptitude": 0.30},
    "anxious":     {"pleasantness": 0.20, "attention": 0.55, "sensitivity": 0.90, "aptitude": 0.25},
    "disengaged":  {"pleasantness": 0.35, "attention": 0.15, "sensitivity": 0.25, "aptitude": 0.20},
    "overwhelmed": {"pleasantness": 0.10, "attention": 0.30, "sensitivity": 0.85, "aptitude": 0.15},
}


def blend_pase(label: str, confidence: float) -> dict[str, float]:
    """Blend a canonical PASE profile toward neutral (0.5) based on confidence.

    High confidence (>0.8) → use canonical profile almost as-is.
    Low confidence (~0.5) → shrink toward neutral center.
    """
    canonical = SETFIT_TO_PASE.get(label, SETFIT_TO_PASE["disengaged"])
    neutral = 0.5
    return {k: round(neutral + (v - neutral) * confidence, 3) for k, v in canonical.items()}


# Singleton: loads model from disk at import time
setfit_classifier = SetFitEmotionClassifier()
setfit_classifier.load()
logger.info("SetFit emotion classifier singleton ready")

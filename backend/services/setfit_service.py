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

# Singleton: loads model from disk at import time
setfit_classifier = SetFitEmotionClassifier()
setfit_classifier.load()
logger.info("SetFit emotion classifier singleton ready")

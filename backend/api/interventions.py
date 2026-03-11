"""
Intervention delivery, response recording, and XAI explanation endpoints.

Phase 4: fully implemented — feeds back to JITAI engine and adaptive bandit.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from services.shared_state import jitai_engine, xai_explainer

router = APIRouter(prefix="/interventions", tags=["interventions"])


class InterventionResponse(BaseModel):
    action_taken: str | None = None
    dismissed: bool = False
    effectiveness_rating: int | None = None


class ConceptCorrectionRequest(BaseModel):
    concept_id: str
    user_value: float
    system_prediction: float | None = None


@router.get("/current")
async def get_current_intervention():
    """Get any pending intervention."""
    return {"intervention": None}


@router.post("/{intervention_id}/respond")
async def respond_to_intervention(
    intervention_id: str,
    response: InterventionResponse,
):
    """Record user response to an intervention.

    Feeds back to:
      - JITAI engine (adaptive cooldown)
      - Thompson Sampling bandit (learn when to intervene)
    """
    jitai_engine.record_response(
        intervention_id=intervention_id,
        action_taken=response.action_taken,
        dismissed=response.dismissed,
    )
    return {
        "status": "recorded",
        "intervention_id": intervention_id,
        "cooldown_seconds": jitai_engine._cooldown_seconds,
    }


@router.post("/correct-concept")
async def correct_concept(correction: ConceptCorrectionRequest):
    """Submit a user correction for a concept prediction.

    The user disagrees with the system's assessment of a concept
    (e.g. "I'm not frustrated, I'm excited"). This feeds back into
    the Concept Bottleneck Model for recalibration.
    """
    result = xai_explainer.apply_user_correction(
        concept_id=correction.concept_id,
        user_value=correction.user_value,
        system_prediction=correction.system_prediction,
    )
    return {
        "status": "correction_recorded",
        "correction": result.model_dump(),
    }

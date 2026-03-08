"""Intervention delivery + response endpoints — stubs for Phase 1, implemented in Phase 4."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/interventions", tags=["interventions"])


class InterventionResponse(BaseModel):
    action_taken: str
    dismissed: bool = False
    effectiveness_rating: int | None = None


@router.get("/current")
async def get_current_intervention():
    """Get any pending intervention (stub)."""
    return {"intervention": None}


@router.post("/{intervention_id}/respond")
async def respond_to_intervention(intervention_id: str, response: InterventionResponse):
    """Record user response to an intervention (stub)."""
    return {
        "status": "recorded",
        "cooldown_seconds": 300,
    }

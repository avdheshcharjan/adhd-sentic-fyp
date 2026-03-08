"""Pydantic models for ADHD interventions."""

from pydantic import BaseModel


class InterventionAction(BaseModel):
    """A single actionable button shown to the user."""

    id: str
    emoji: str
    label: str


class Intervention(BaseModel):
    """An ADHD-aware intervention delivered to the user."""

    type: str
    ef_domain: str
    acknowledgment: str
    suggestion: str
    actions: list[InterventionAction]
    requires_senticnet: bool = False

"""Pydantic models for ADHD interventions."""

import uuid
from pydantic import BaseModel, Field


class InterventionAction(BaseModel):
    """A single actionable button shown to the user.

    Anti-pattern #8: NEVER show more than 3 action choices per intervention.
    """

    id: str
    emoji: str
    label: str


class Intervention(BaseModel):
    """An ADHD-aware intervention delivered to the user.

    Anti-pattern #5: Always upward framing — never guilt/shame.
    Anti-pattern #8: Max 3 actions.
    Anti-pattern #10: urgency_color uses warm spectrum (green→amber→orange→red),
                      never blue.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    ef_domain: str
    acknowledgment: str
    suggestion: str
    actions: list[InterventionAction]
    requires_senticnet: bool = False

    # Phase 4 additions
    notification_tier: int = 3  # 1-5, from notification_tier.select_tier()
    urgency_color: str = "amber"  # green | amber | orange | red (warm spectrum)
    explanation: dict | None = None  # XAI explanation payload (3-tier progressive)

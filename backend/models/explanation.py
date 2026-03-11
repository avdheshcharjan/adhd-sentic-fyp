"""Pydantic models for XAI explanations and concept corrections."""

from datetime import datetime
from pydantic import BaseModel, Field


class ExplanationTier1(BaseModel):
    """Traffic-light indicator + emoji — always visible."""

    color: str = "green"  # green | amber | orange | red (warm spectrum, never blue)
    emoji: str = "💡"


class ExplanationTier2(BaseModel):
    """One-sentence concept explanation — shown on first tap."""

    sentence: str = ""


class ExplanationTier3Detail(BaseModel):
    """Single concept detail with optional user correction."""

    concept: str
    value: float
    description: str
    can_correct: bool = False
    correction_prompt: str | None = None


class ExplanationTier3(BaseModel):
    """Full breakdown with correction option — shown on second tap."""

    concepts: list[ExplanationTier3Detail] = Field(default_factory=list)


class InterventionExplanation(BaseModel):
    """3-tier progressive disclosure explanation for an intervention.

    Anti-pattern #3: NEVER auto-expand. User pulls deeper info when ready.
    """

    what: str = ""  # Behavioural observation
    why: str = ""   # SenticNet/concept-level reasoning
    how: str = ""   # Counterfactual — what would improve things

    tier_1: ExplanationTier1 = Field(default_factory=ExplanationTier1)
    tier_2: ExplanationTier2 = Field(default_factory=ExplanationTier2)
    tier_3: ExplanationTier3 = Field(default_factory=ExplanationTier3)


class ConceptCorrection(BaseModel):
    """User correction of a concept prediction (feeds back into CBM)."""

    concept_id: str
    system_prediction: float | None = None
    user_correction: float
    timestamp: datetime = Field(default_factory=datetime.now)

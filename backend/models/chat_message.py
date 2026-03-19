"""Pydantic models for chat/venting messages."""

from pydantic import BaseModel


class ChatInput(BaseModel):
    """Input from OpenClaw or Dashboard chat."""

    text: str
    conversation_id: str | None = None
    context: dict | None = None


class EmotionDetail(BaseModel):
    """SenticNet analysis output, included in response for evaluation."""

    polarity: float = 0.0                        # Overall sentiment polarity [-1, 1]
    mood_tags: list[str] = []                     # e.g., ["#frustrated", "#anxious"]
    hourglass_pleasantness: float = 0.0           # [-1, 1] (introspection)
    hourglass_attention: float = 0.0              # [-1, 1] (temper)
    hourglass_sensitivity: float = 0.0            # [-1, 1]
    hourglass_aptitude: float = 0.0               # [-1, 1] (attitude)
    sentic_concepts: list[str] = []               # Top matched SenticNet concepts


class ChatResponse(BaseModel):
    """Response with LLM reply + optional emotional analysis."""

    response: str
    emotion_profile: dict | None = None
    safety_flags: dict | None = None
    suggested_actions: list[dict] | None = None
    used_llm: bool = False
    thinking_mode: str | None = None
    emotion_context: EmotionDetail | None = None  # Populated when SenticNet is active
    ablation_mode: bool = False                    # Indicates if SenticNet was bypassed
    latency_ms: float = 0.0                        # End-to-end processing time
    token_count: int = 0                           # LLM tokens generated

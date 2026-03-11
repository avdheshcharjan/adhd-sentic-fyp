"""Pydantic models for chat/venting messages."""

from pydantic import BaseModel


class ChatInput(BaseModel):
    """Input from OpenClaw or Dashboard chat."""

    text: str
    conversation_id: str | None = None
    context: dict | None = None


class ChatResponse(BaseModel):
    """Response with LLM reply + optional emotional analysis."""

    response: str
    emotion_profile: dict | None = None
    safety_flags: dict | None = None
    suggested_actions: list[dict] | None = None
    used_llm: bool = False
    thinking_mode: str | None = None

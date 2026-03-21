"""Pydantic v2 models for Vent chat feature."""

from pydantic import BaseModel, Field


class VentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


class VentChatResponse(BaseModel):
    response: str
    emotional_state: str | None = None
    is_crisis: bool = False

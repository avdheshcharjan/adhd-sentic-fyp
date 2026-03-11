"""
Chat/venting endpoint — full pipeline: SenticNet -> Safety -> LLM -> Memory.
"""

from fastapi import APIRouter

from models.chat_message import ChatInput, ChatResponse
from services.chat_processor import ChatProcessor
from services.constants import CRISIS_RESOURCES_SG

router = APIRouter(prefix="/chat", tags=["chat"])

_processor = ChatProcessor()


@router.post("/message", response_model=ChatResponse)
async def process_message(message: ChatInput):
    """
    Process a venting/chat message through the full pipeline.

    Pipeline:
      1. SenticNet emotion analysis
      2. Safety check (crisis -> resources, no LLM)
      3. Qwen3-4B coaching response via MLX
      4. Mem0 memory storage
    """
    result = await _processor.process_vent_message(
        text=message.text,
        conversation_id=message.conversation_id,
    )

    suggested_actions = _get_suggested_actions(result)

    return ChatResponse(
        response=result["response"],
        emotion_profile=result.get("senticnet"),
        safety_flags=None,
        suggested_actions=suggested_actions,
        used_llm=result["used_llm"],
        thinking_mode=result.get("thinking_mode"),
    )


def _get_suggested_actions(result: dict) -> list[dict]:
    """Generate suggested actions based on pipeline result."""
    if not result["used_llm"]:
        return [
            {"id": r["id"], "label": r["label"]}
            for r in CRISIS_RESOURCES_SG
        ]

    senticnet = result.get("senticnet", {})
    intensity = abs(senticnet.get("intensity_score", 0))
    engagement = senticnet.get("engagement_score", 0)

    actions = []
    if intensity > 60:
        actions.append({"id": "breathe", "label": "2-minute breathing exercise"})
    if engagement < -30:
        actions.append({"id": "smallest_step", "label": "Pick the smallest next step"})
    if intensity < -50:
        actions.append({"id": "break", "label": "Take a short break"})

    if not actions:
        actions = [
            {"id": "continue", "label": "Tell me more"},
            {"id": "breathe", "label": "Quick breathing"},
            {"id": "break", "label": "Take a break"},
        ]

    return actions[:3]

"""Chat/venting endpoint — stub for Phase 1, implemented in Phase 3."""

from fastapi import APIRouter

from models.chat_message import ChatInput, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def process_message(message: ChatInput):
    """
    Process a venting/chat message (stub).
    Full SenticNet pipeline + LLM generation added in Phase 3.
    """
    return ChatResponse(
        response="Chat processing is not yet implemented. Coming in Phase 3 (SenticNet Pipeline).",
        emotion_profile=None,
        safety_flags=None,
        suggested_actions=None,
    )

"""Vent chat API router — /api/v1/vent endpoints with SSE streaming."""

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.vent_models import VentChatRequest, VentChatResponse
from services.memory_service import memory_service
from services.senticnet_pipeline import SenticNetPipeline
from services.vent_service import VentService

logger = logging.getLogger("adhd-brain.api.vent")

router = APIRouter(prefix="/api/v1/vent", tags=["vent"])

# Service singleton — initialized on first request
_service: VentService | None = None


def _get_service() -> VentService:
    global _service
    if _service is None:
        from services.mlx_inference import mlx_inference

        _service = VentService(
            llm=mlx_inference,
            senticnet=SenticNetPipeline(),
            memory=memory_service,
        )
    return _service


@router.post("/chat/stream")
async def vent_chat_stream(request: VentChatRequest):
    """SSE streaming endpoint for vent chat responses."""
    service = _get_service()

    async def event_stream():
        async for chunk in service.stream_response(
            message=request.message,
            session_id=request.session_id,
            history=request.history,
        ):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat", response_model=VentChatResponse)
async def vent_chat(request: VentChatRequest):
    """Non-streaming endpoint (fallback). Collects full response."""
    service = _get_service()
    full_response = ""
    is_crisis = False

    async for chunk in service.stream_response(
        message=request.message,
        session_id=request.session_id,
        history=request.history,
    ):
        full_response += chunk

    if "988 Suicide & Crisis Lifeline" in full_response:
        is_crisis = True

    return VentChatResponse(response=full_response, is_crisis=is_crisis)


@router.post("/session/new")
async def new_session(session_id: str):
    """Clear session state when user starts a new vent session."""
    service = _get_service()
    service.clear_session(session_id)
    return {"status": "ok", "message": "Session cleared"}

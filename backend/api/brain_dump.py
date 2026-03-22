"""Brain Dump API router — /api/v1/brain-dump endpoints."""

import json
import logging
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.brain_dump_models import (
    BrainDumpRequest,
    BrainDumpResponse,
    BrainDumpReviewItem,
    BrainDumpReviewResponse,
)
from services.brain_dump_service import BrainDumpService
from services.memory_service import memory_service
from services.shared_state import brain_dump_reminders
from services.senticnet_pipeline import SenticNetPipeline

logger = logging.getLogger("adhd-brain.api.brain-dump")

router = APIRouter(prefix="/api/v1/brain-dump", tags=["brain-dump"])

# Service singleton — initialized on first request
_service: BrainDumpService | None = None


def _get_service() -> BrainDumpService:
    global _service
    if _service is None:
        from services.mlx_inference import mlx_inference

        _service = BrainDumpService(
            memory=memory_service,
            senticnet=SenticNetPipeline(),
            llm=mlx_inference,
        )
    return _service


@router.post("/", response_model=BrainDumpResponse)
async def capture_brain_dump(request: BrainDumpRequest):
    """Capture a brain dump entry. Stores in Mem0 with SenticNet emotion tagging."""
    service = _get_service()
    result = await service.capture(
        content=request.content,
        user_id="default_user",
        session_id=request.session_id,
    )

    # Queue for JITAI reminder when user is idle
    brain_dump_reminders.add(entry_id=result["id"], content=request.content)

    return BrainDumpResponse(**result)


@router.post("/stream")
async def capture_brain_dump_stream(request: BrainDumpRequest):
    """Capture a brain dump and stream an AI summary back via SSE."""
    service = _get_service()

    # First capture the brain dump (store in Mem0)
    result = await service.capture(
        content=request.content,
        user_id="default_user",
        session_id=request.session_id,
    )

    # Queue for JITAI reminder when user is idle
    brain_dump_reminders.add(entry_id=result["id"], content=request.content)

    async def event_stream():
        # Emit the capture confirmation first
        yield f"data: {json.dumps({'type': 'captured', 'id': result['id'], 'emotional_state': result.get('emotional_state')})}\n\n"

        # Stream the AI summary
        async for chunk in service.stream_summary(
            content=request.content,
            emotional_state=result.get("emotional_state"),
        ):
            yield f"data: {json.dumps({'type': 'summary', 'token': chunk})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/review/session/{session_id}", response_model=BrainDumpReviewResponse)
async def review_session_dumps(session_id: str):
    """Retrieve brain dumps for a completed focus session (dashboard review)."""
    service = _get_service()
    raw_items = service.get_session_dumps(user_id="default_user", session_id=session_id)

    items = _parse_review_items(raw_items, session_id)
    return BrainDumpReviewResponse(items=items, count=len(items))


@router.get("/review/recent", response_model=BrainDumpReviewResponse)
async def review_recent_dumps(limit: int = 20):
    """Retrieve recent brain dumps regardless of session."""
    service = _get_service()
    raw_items = service.get_recent_dumps(user_id="default_user", limit=limit)

    items = _parse_review_items(raw_items)
    return BrainDumpReviewResponse(items=items, count=len(items))


def _parse_review_items(
    raw_items: list[dict],
    default_session_id: str | None = None,
) -> list[BrainDumpReviewItem]:
    """Parse Mem0 search results into BrainDumpReviewItem list."""
    items = []
    for r in raw_items:
        context = r.get("metadata", {}).get("context", "")
        parts = context.split("|") if context else []
        # context format: "brain_dump|entry_id|session_id|emotional_state|timestamp"
        items.append(
            BrainDumpReviewItem(
                id=parts[1] if len(parts) > 1 else "unknown",
                content=r.get("memory", r.get("text", "")),
                emotional_state=parts[3] if len(parts) > 3 and parts[3] != "unknown" else None,
                timestamp=datetime.fromisoformat(parts[4]) if len(parts) > 4 else datetime.now(),
                session_id=parts[2] if len(parts) > 2 and parts[2] != "none" else default_session_id,
            )
        )
    return items

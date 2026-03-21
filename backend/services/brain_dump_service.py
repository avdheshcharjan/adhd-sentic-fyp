"""
Brain Dump service — stores entries in Mem0 with SenticNet emotional tagging.

Flow:
1. Receive raw text from user
2. Run text through SenticNet for emotion detection (non-blocking)
3. Store in Mem0 with metadata: type=brain_dump, session_id, emotional_state, timestamp
4. Return confirmation immediately
"""

import logging
import uuid
from datetime import datetime, timezone

from services.memory_service import MemoryService
from services.senticnet_pipeline import SenticNetPipeline

logger = logging.getLogger("adhd-brain.brain-dump")


class BrainDumpService:
    def __init__(self, memory: MemoryService, senticnet: SenticNetPipeline):
        self.memory = memory
        self.senticnet = senticnet

    async def capture(
        self,
        content: str,
        user_id: str,
        session_id: str | None = None,
    ) -> dict:
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        # Run SenticNet lightweight emotion analysis (don't block on failure)
        emotional_state: str | None = None
        try:
            result = await self.senticnet.analyze(content, mode="lightweight")
            emotional_state = result.emotion.primary_emotion
        except Exception as e:
            logger.warning(f"SenticNet analysis failed for brain dump: {e}")

        # Store in Mem0 (synchronous call — mem0 is not async-native)
        try:
            self.memory.add_conversation_memory(
                user_id=user_id,
                message=content,
                context=f"brain_dump|{entry_id}|{session_id or 'none'}|{emotional_state or 'unknown'}|{timestamp.isoformat()}",
            )
            logger.info(f"Brain dump captured: {entry_id}")
        except Exception as e:
            logger.error(f"Failed to store brain dump in Mem0: {e}")

        return {
            "id": entry_id,
            "status": "captured",
            "emotional_state": emotional_state,
            "timestamp": timestamp,
        }

    def get_session_dumps(self, user_id: str, session_id: str) -> list[dict]:
        """Retrieve brain dumps for a completed focus session."""
        results = self.memory.search_relevant_context(
            user_id=user_id,
            query=f"brain_dump session {session_id}",
            limit=50,
        )
        return [
            r for r in results
            if "brain_dump" in r.get("metadata", {}).get("context", "")
            and session_id in r.get("metadata", {}).get("context", "")
        ]

    def get_recent_dumps(self, user_id: str, limit: int = 20) -> list[dict]:
        """Retrieve recent brain dumps regardless of session."""
        results = self.memory.search_relevant_context(
            user_id=user_id,
            query="brain_dump",
            limit=limit,
        )
        return [
            r for r in results
            if "brain_dump" in r.get("metadata", {}).get("context", "")
        ]

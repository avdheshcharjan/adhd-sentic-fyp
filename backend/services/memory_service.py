import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from mem0 import Memory

from config import get_settings
from db.models import BehavioralPattern, InterventionHistory
from db.repositories.pattern_repo import pattern_repo

settings = get_settings()
logger = logging.getLogger("adhd-brain.memory_service")

class MemoryService:
    """
    Dual-Layer Memory Service:
    - Layer 1: Conversational & semantic memory using Mem0 (backed by pgvector)
    - Layer 2: Behavioral & Explicit tracking using PostgreSQL pattern_repo
    """

    def __init__(self):
        self.mem0 = None
        self._initialize_mem0()

    def _initialize_mem0(self):
        """Initializes mem0ai with pgvector."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. Mem0 will run in limited/mock mode if at all.")
            
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "api_key": settings.OPENAI_API_KEY
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": settings.OPENAI_API_KEY
                }
            },
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "dbname": "adhd_brain",
                    "user": "adhd",
                    "password": "adhd",
                    "host": "localhost",
                    "port": 5433,
                    "collection_name": "adhd_memories"
                }
            },
            # NOTE: Mem0 reranker and custom_fact_extraction_prompt configs
            # were attempted (fixes 4.2, 4.5) but are incompatible with the
            # current Mem0 version — they cause 'dict' object has no attribute
            # 'replace' errors during mem0.add(). Reverted to default config.
        }
        
        try:
            self.mem0 = Memory.from_config(config)
            logger.info("✅ Mem0 initialized with pgvector backend")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            # Keep as null, logic should handle graceful degradation

    # ── Layer 1: Conversational Memory (Mem0) ───────────────────────────────────

    def add_conversation_memory(
        self,
        user_id: str,
        message: str,
        context: Optional[str] = None,
        memory_type: str = "conversation",
    ):
        """
        Store chat context after a vent session or regular interaction.

        Args:
            memory_type: "conversation", "strategy", "problem", "trigger", or "preference"
        """
        if not self.mem0:
            logger.warning("Mem0 is not initialized, skipping conversation memory.")
            return

        metadata = {"type": memory_type}
        if context:
            metadata["context"] = context

        try:
            # Note: mem0 add() blocks/is synchronous natively unless wrapped
            self.mem0.add(message, user_id=user_id, metadata=metadata)
            logger.info(f"Added {memory_type} memory for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding conversation memory: {e}")

    def search_relevant_context(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context for LLM injection.

        Args:
            memory_type: Optional filter — "conversation", "strategy", "problem", etc.
        """
        if not self.mem0:
            return []

        try:
            kwargs: Dict[str, Any] = {"user_id": user_id, "limit": limit}
            if memory_type:
                kwargs["filters"] = {"type": memory_type}
            results = self.mem0.search(query, **kwargs)
            if isinstance(results, dict) and "results" in results:
                return results["results"]
            return results
        except Exception as e:
            logger.error(f"Error searching memory context: {e}")
            return []

    # ── Layer 2: Behavioral Patterns (PostgreSQL) ───────────────────────────────

    async def add_pattern_memory(
        self, db: AsyncSession, pattern_type: str, description: str, 
        confidence: float = 1.0, source_evidence: List[str] = None
    ) -> BehavioralPattern:
        """
        Store detected behavioral patterns into persistent DB store.
        """
        pattern_data = {
            "pattern_type": pattern_type,
            "description": description,
            "detected_at": datetime.now(timezone.utc),
            "confidence": confidence,
            "source_evidence": source_evidence or []
        }
        pattern = await pattern_repo.create(db, pattern_data)
        logger.info(f"Stored pattern memory type '{pattern_type}' (id: {pattern.id})")
        
        # Dual-store: also add high-level summary to conversational memory if high confidence
        if confidence > 0.8 and self.mem0:
            self.mem0.add(
                f"Observed highly confident pattern: {description}", 
                user_id="default_user", 
                metadata={"type": "pattern", "pattern_id": str(pattern.id)}
            )
            
        return pattern

    async def get_intervention_history(
        self, db: AsyncSession, limit: int = 10, intervention_type: Optional[str] = None
    ) -> List[InterventionHistory]:
        """
        Retrieve past intervention responses.
        Which interventions worked?
        """
        return await pattern_repo.get_intervention_history(
            db=db, limit=limit, intervention_type=intervention_type
        )

# Singleton
memory_service = MemoryService()

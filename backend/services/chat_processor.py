"""
Full chat processing pipeline.

SenticNet detects emotion (hard part) -> LLM generates response (easy part).
Safety check is non-negotiable and runs FIRST.
"""

import logging
from typing import Optional

from services.senticnet_pipeline import SenticNetPipeline
from services.mlx_inference import mlx_inference
from services.memory_service import memory_service
from services.constants import (
    ADHD_COACHING_SYSTEM_PROMPT,
    CRISIS_RESOURCES_SG,
    CRISIS_RESPONSE_TEXT,
)

logger = logging.getLogger("adhd-brain.chat")


class ChatProcessor:
    """Orchestrates the full chat pipeline: SenticNet -> Safety -> LLM -> Memory."""

    def __init__(self):
        self.pipeline = SenticNetPipeline()
        self._mlx = mlx_inference
        self._memory = memory_service

    async def process_vent_message(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        user_id: str = "default_user",
    ) -> dict:
        """
        Full pipeline for processing a user's venting/chat message.

        1. SenticNet analysis (fast, deterministic)
        2. Safety check (non-negotiable, runs FIRST)
        3. Build structured context for LLM
        4. Determine /think vs /no_think mode
        5. Generate response via MLX
        6. Store in Mem0
        """
        # Step 1: SenticNet analysis
        result = await self.pipeline.analyze(text=text, mode="full")

        # Step 2: Safety check — critical = no LLM, just compassion + resources
        if result.safety.is_critical:
            return {
                "response": CRISIS_RESPONSE_TEXT,
                "resources": CRISIS_RESOURCES_SG,
                "senticnet": self._build_senticnet_context(result),
                "used_llm": False,
                "thinking_mode": None,
            }

        # Step 3: Build structured context
        senticnet_context = self._build_senticnet_context(result)

        # Step 4: Determine thinking mode
        use_thinking = (
            abs(result.adhd_signals.intensity_score) > 60
            or "help" in text.lower()
            or len(text) > 200
        )

        # Step 5: Generate response via MLX
        response = self._mlx.generate_coaching_response(
            system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
            user_message=text,
            senticnet_context=senticnet_context,
            use_thinking=use_thinking,
        )

        # Step 6: Store in memory
        try:
            self._memory.add_conversation_memory(
                user_id=user_id,
                message=f"User: {text}\nAssistant: {response}",
                context=str(senticnet_context),
            )
        except Exception as e:
            logger.warning(f"Failed to store conversation memory: {e}")

        return {
            "response": response,
            "senticnet": senticnet_context,
            "used_llm": True,
            "thinking_mode": "think" if use_thinking else "no_think",
        }

    def _build_senticnet_context(self, result) -> dict:
        """Extract structured context from SenticNetResult for LLM injection."""
        return {
            "primary_emotion": result.emotion.primary_emotion,
            "introspection": result.emotion.introspection,
            "temper": result.emotion.temper,
            "attitude": result.emotion.attitude,
            "sensitivity": result.emotion.sensitivity,
            "intensity_score": result.adhd_signals.intensity_score,
            "engagement_score": result.adhd_signals.engagement_score,
            "wellbeing_score": result.adhd_signals.wellbeing_score,
            "safety_level": result.safety.level,
            "concepts": result.adhd_signals.concepts[:5],
        }

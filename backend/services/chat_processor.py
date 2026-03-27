"""
Full chat processing pipeline.

SenticNet detects emotion (hard part) -> LLM generates response (easy part).
Safety check is non-negotiable and runs FIRST.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import psutil

from config import get_settings
from services.senticnet_pipeline import SenticNetPipeline
from services.memory_service import memory_service
from services.evaluation_logger import EvaluationLogger, EvaluationLogEntry
from services.constants import (
    ADHD_COACHING_SYSTEM_PROMPT,
    ADHD_COACHING_SYSTEM_PROMPT_VANILLA,
    CRISIS_RESOURCES_SG,
    CRISIS_RESPONSE_TEXT,
)

logger = logging.getLogger("adhd-brain.chat")
settings = get_settings()


class ChatProcessor:
    """Orchestrates the full chat pipeline: SenticNet -> Safety -> LLM -> Memory."""

    def __init__(self):
        self.pipeline = SenticNetPipeline()
        self._mlx = None
        self._memory = memory_service
        self._eval_logger = EvaluationLogger(settings.EVALUATION_LOG_PATH)
        self._process = psutil.Process()

    def _get_mlx(self):
        """Lazy-load MLX inference to avoid import-time dependency on mlx_lm."""
        if self._mlx is None:
            from services.mlx_inference import mlx_inference
            self._mlx = mlx_inference
        return self._mlx

    async def process_vent_message(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        user_id: str = "default_user",
    ) -> dict:
        """
        Full pipeline for processing a user's venting/chat message.

        1. SenticNet analysis (skip if ablation mode)
        2. Safety check (non-negotiable, runs FIRST — skipped in ablation)
        3. Build structured context for LLM
        4. Determine /think vs /no_think mode
        5. Generate response via MLX (timed for evaluation)
        6. Log for evaluation if enabled
        7. Store in Mem0
        """
        pipeline_start = time.perf_counter()
        ablation_mode = settings.ABLATION_MODE

        # Step 1: SenticNet analysis (skip if ablation mode)
        result = None
        senticnet_context = None
        sentic_latency_ms = None
        if not ablation_mode:
            sentic_start = time.perf_counter()
            result = await self.pipeline.analyze(text=text, mode="full")
            sentic_latency_ms = (time.perf_counter() - sentic_start) * 1000

            # Step 2: Safety check — critical = no LLM, just compassion + resources
            if result.safety.is_critical:
                return {
                    "response": CRISIS_RESPONSE_TEXT,
                    "resources": CRISIS_RESOURCES_SG,
                    "senticnet": self._build_senticnet_context(result),
                    "used_llm": False,
                    "thinking_mode": None,
                    "ablation_mode": False,
                    "latency_ms": 0.0,
                    "token_count": 0,
                }

            # Step 3: Build structured context
            senticnet_context = self._build_senticnet_context(result)

        # Step 4: Determine thinking mode
        if result is not None:
            use_thinking = (
                abs(result.adhd_signals.intensity_score) > 60
                or "help" in text.lower()
                or len(text) > 200
            )
        else:
            # Ablation mode: simple heuristic without SenticNet
            use_thinking = "help" in text.lower() or len(text) > 200

        # Step 5: Select system prompt based on ablation mode
        system_prompt = (
            ADHD_COACHING_SYSTEM_PROMPT_VANILLA if ablation_mode
            else ADHD_COACHING_SYSTEM_PROMPT
        )

        # Step 6: Generate response via MLX (timed)
        llm_start = time.perf_counter()
        response = self._get_mlx().generate_coaching_response(
            system_prompt=system_prompt,
            user_message=text,
            senticnet_context=senticnet_context,  # None when ablation mode
            use_thinking=use_thinking,
        )
        llm_generation_ms = (time.perf_counter() - llm_start) * 1000

        # Estimate token count (rough: 4 chars per token)
        token_count = len(response) // 4
        tokens_per_second = (token_count / (llm_generation_ms / 1000)) if llm_generation_ms > 0 else 0.0

        pipeline_total_ms = (time.perf_counter() - pipeline_start) * 1000

        # Step 7: Log for evaluation if enabled (fire-and-forget)
        if settings.EVALUATION_LOGGING:
            asyncio.create_task(self._log_evaluation_data(
                user_message=text,
                senticnet_context=senticnet_context,
                result=result,
                response=response,
                ablation_mode=ablation_mode,
                conversation_id=conversation_id or "unknown",
                sentic_latency_ms=sentic_latency_ms,
                llm_generation_ms=llm_generation_ms,
                token_count=token_count,
                tokens_per_second=tokens_per_second,
                pipeline_total_ms=pipeline_total_ms,
                thinking_mode="think" if use_thinking else "no_think",
            ))

        # Step 8: Store in memory
        try:
            self._memory.add_conversation_memory(
                user_id=user_id,
                message=f"User: {text}\nAssistant: {response}",
                context=str(senticnet_context) if senticnet_context else "",
            )
        except Exception as e:
            logger.warning(f"Failed to store conversation memory: {e}")

        return {
            "response": response,
            "senticnet": senticnet_context,
            "used_llm": True,
            "thinking_mode": "think" if use_thinking else "no_think",
            "ablation_mode": ablation_mode,
            "latency_ms": pipeline_total_ms,
            "token_count": token_count,
        }

    def _build_senticnet_context(self, result) -> dict:
        """Extract structured context from SenticNetResult for LLM injection."""
        return {
            "primary_emotion": result.emotion.primary_emotion,
            "introspection": result.emotion.introspection,
            "temper": result.emotion.temper,
            "attitude": result.emotion.attitude,
            "sensitivity": result.emotion.sensitivity,
            "polarity_score": result.emotion.polarity_score,
            "intensity_score": result.adhd_signals.intensity_score,
            "engagement_score": result.adhd_signals.engagement_score,
            "wellbeing_score": result.adhd_signals.wellbeing_score,
            "safety_level": result.safety.level,
            "concepts": result.adhd_signals.concepts[:5],
            "primary_adhd_state": result.primary_adhd_state,
        }

    async def _log_evaluation_data(
        self,
        user_message: str,
        senticnet_context: dict | None,
        result,
        response: str,
        ablation_mode: bool,
        conversation_id: str,
        sentic_latency_ms: float | None,
        llm_generation_ms: float,
        token_count: int,
        tokens_per_second: float,
        pipeline_total_ms: float,
        thinking_mode: str,
    ) -> None:
        """Log interaction data for evaluation analysis."""
        # Capture system state snapshot
        try:
            rss_mb = self._process.memory_info().rss / (1024 * 1024)
            cpu_pct = self._process.cpu_percent(interval=None)
        except Exception:
            rss_mb = None
            cpu_pct = None

        safety_triggered = False
        if result is not None and result.safety.is_critical:
            safety_triggered = True

        entry = EvaluationLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id=conversation_id,
            session_id=conversation_id.split("_")[0] if conversation_id else "default",
            ablation_mode=ablation_mode,
            user_message=user_message,
            user_message_length=len(user_message),
            user_message_word_count=len(user_message.split()),
            sentic_polarity=(
                senticnet_context.get("polarity_score") if senticnet_context else None
            ),
            sentic_mood_tags=(
                [senticnet_context.get("primary_emotion", "")]
                if senticnet_context else None
            ),
            hourglass_pleasantness=(
                senticnet_context.get("introspection") if senticnet_context else None
            ),
            hourglass_attention=(
                senticnet_context.get("temper") if senticnet_context else None
            ),
            hourglass_sensitivity=(
                senticnet_context.get("sensitivity") if senticnet_context else None
            ),
            hourglass_aptitude=(
                senticnet_context.get("attitude") if senticnet_context else None
            ),
            sentic_latency_ms=sentic_latency_ms,
            llm_response=response,
            llm_response_length=len(response),
            llm_response_token_count=token_count,
            llm_generation_ms=llm_generation_ms,
            llm_tokens_per_second=tokens_per_second,
            llm_thinking_mode=thinking_mode,
            pipeline_total_ms=pipeline_total_ms,
            safety_input_triggered=safety_triggered,
            system_memory_rss_mb=rss_mb,
            system_cpu_percent=cpu_pct,
        )
        try:
            await self._eval_logger.log(entry)
        except Exception as e:
            logger.warning(f"Failed to log evaluation data: {e}")

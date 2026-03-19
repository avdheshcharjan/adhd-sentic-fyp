"""Tests for chat processor pipeline."""

import sys
from unittest.mock import MagicMock
sys.modules.setdefault("mlx_lm", MagicMock())

import pytest
from unittest.mock import AsyncMock, patch


def _make_senticnet_result(is_critical=False, safety_level="normal",
                            primary_emotion="neutral", intensity=0.0,
                            engagement=0.0, wellbeing=0.0):
    """Helper to build a mock SenticNetResult."""
    result = MagicMock()
    result.safety.is_critical = is_critical
    result.safety.level = safety_level
    result.safety.depression_score = 0.0
    result.safety.toxicity_score = 0.0
    result.safety.intensity_score = intensity
    result.emotion.primary_emotion = primary_emotion
    result.emotion.introspection = 0.0
    result.emotion.temper = 0.0
    result.emotion.attitude = 0.0
    result.emotion.sensitivity = 0.0
    result.emotion.polarity_score = 0.0
    result.adhd_signals.intensity_score = intensity
    result.adhd_signals.engagement_score = engagement
    result.adhd_signals.wellbeing_score = wellbeing
    result.adhd_signals.concepts = ["work", "stress"]
    result.adhd_signals.is_overwhelmed = False
    result.adhd_signals.is_disengaged = False
    result.adhd_signals.is_frustrated = False
    result.adhd_signals.emotional_dysregulation = False
    return result


class TestChatProcessorSafety:
    @pytest.mark.asyncio
    async def test_critical_safety_returns_crisis_resources_no_llm(self):
        from services.chat_processor import ChatProcessor
        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result(
            is_critical=True, safety_level="critical"
        )

        result = await proc.process_vent_message("I want to end it all")

        assert result["used_llm"] is False
        assert "resources" in result
        assert len(result["resources"]) == 3
        proc._mlx.generate_coaching_response.assert_not_called()


class TestChatProcessorLLM:
    @pytest.mark.asyncio
    async def test_normal_message_uses_llm(self):
        from services.chat_processor import ChatProcessor
        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="frustration", intensity=40.0
        )
        proc._mlx.generate_coaching_response.return_value = "I hear your frustration."

        result = await proc.process_vent_message("I can't focus on anything today")

        assert result["used_llm"] is True
        assert result["response"] == "I hear your frustration."
        proc._mlx.generate_coaching_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_high_intensity_uses_think_mode(self):
        from services.chat_processor import ChatProcessor
        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="anger", intensity=75.0
        )
        proc._mlx.generate_coaching_response.return_value = "That sounds really tough."

        result = await proc.process_vent_message("Everything is falling apart")

        assert result["thinking_mode"] == "think"
        call_kwargs = proc._mlx.generate_coaching_response.call_args[1]
        assert call_kwargs["use_thinking"] is True

    @pytest.mark.asyncio
    async def test_low_intensity_uses_no_think_mode(self):
        from services.chat_processor import ChatProcessor
        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="boredom", intensity=20.0
        )
        proc._mlx.generate_coaching_response.return_value = "Let's find something engaging."

        result = await proc.process_vent_message("Meh")

        assert result["thinking_mode"] == "no_think"


class TestChatProcessorMemory:
    @pytest.mark.asyncio
    async def test_stores_conversation_in_memory(self):
        from services.chat_processor import ChatProcessor
        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result()
        proc._mlx.generate_coaching_response.return_value = "I'm here for you."

        await proc.process_vent_message("I feel stuck")

        proc._memory.add_conversation_memory.assert_called_once()


class TestChatProcessorAblation:
    @pytest.mark.asyncio
    async def test_ablation_mode_skips_senticnet(self):
        """When ablation mode is on, SenticNet should not be called."""
        from services.chat_processor import ChatProcessor
        from config import get_settings

        settings = get_settings()
        original = settings.ABLATION_MODE
        settings.ABLATION_MODE = True

        try:
            proc = ChatProcessor()
            proc.pipeline = AsyncMock()
            proc._mlx = MagicMock()
            proc._memory = MagicMock()
            proc._mlx.generate_coaching_response.return_value = "Vanilla response."

            result = await proc.process_vent_message("I can't focus")

            # SenticNet should NOT be called
            proc.pipeline.analyze.assert_not_called()
            # LLM should still be called
            proc._mlx.generate_coaching_response.assert_called_once()
            assert result["used_llm"] is True
            assert result["ablation_mode"] is True
            # senticnet context should be None
            assert result["senticnet"] is None
            # Should include latency and token_count
            assert "latency_ms" in result
            assert "token_count" in result
        finally:
            settings.ABLATION_MODE = original

    @pytest.mark.asyncio
    async def test_ablation_mode_off_calls_senticnet(self):
        """When ablation mode is off, SenticNet should be called normally."""
        from services.chat_processor import ChatProcessor
        from config import get_settings

        settings = get_settings()
        original = settings.ABLATION_MODE
        settings.ABLATION_MODE = False

        try:
            proc = ChatProcessor()
            proc.pipeline = AsyncMock()
            proc._mlx = MagicMock()
            proc._memory = MagicMock()

            proc.pipeline.analyze.return_value = _make_senticnet_result(
                primary_emotion="frustration", intensity=30.0
            )
            proc._mlx.generate_coaching_response.return_value = "I hear you."

            result = await proc.process_vent_message("I'm frustrated")

            proc.pipeline.analyze.assert_called_once()
            assert result["ablation_mode"] is False
            assert result["senticnet"] is not None
        finally:
            settings.ABLATION_MODE = original

    @pytest.mark.asyncio
    async def test_ablation_mode_uses_vanilla_prompt(self):
        """Ablation mode should use the vanilla system prompt without SenticNet references."""
        from services.chat_processor import ChatProcessor
        from services.constants import ADHD_COACHING_SYSTEM_PROMPT_VANILLA
        from config import get_settings

        settings = get_settings()
        original = settings.ABLATION_MODE
        settings.ABLATION_MODE = True

        try:
            proc = ChatProcessor()
            proc.pipeline = AsyncMock()
            proc._mlx = MagicMock()
            proc._memory = MagicMock()
            proc._mlx.generate_coaching_response.return_value = "Vanilla."

            await proc.process_vent_message("Test")

            call_kwargs = proc._mlx.generate_coaching_response.call_args[1]
            assert call_kwargs["system_prompt"] == ADHD_COACHING_SYSTEM_PROMPT_VANILLA
            assert call_kwargs["senticnet_context"] is None
        finally:
            settings.ABLATION_MODE = original

    @pytest.mark.asyncio
    async def test_response_includes_latency_and_tokens(self):
        """Responses should include latency_ms and token_count."""
        from services.chat_processor import ChatProcessor

        proc = ChatProcessor()
        proc.pipeline = AsyncMock()
        proc._mlx = MagicMock()
        proc._memory = MagicMock()

        proc.pipeline.analyze.return_value = _make_senticnet_result()
        proc._mlx.generate_coaching_response.return_value = "I'm here."

        result = await proc.process_vent_message("Hello")

        assert result["latency_ms"] > 0
        assert result["token_count"] >= 0

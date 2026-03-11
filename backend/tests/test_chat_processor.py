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

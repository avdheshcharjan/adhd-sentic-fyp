"""Tests for evaluation API endpoints and ChatResponse model."""

import sys
from unittest.mock import MagicMock
sys.modules.setdefault("mlx_lm", MagicMock())

import pytest
from models.chat_message import ChatResponse, EmotionDetail


class TestEmotionDetail:
    def test_create_with_defaults(self):
        detail = EmotionDetail()
        assert detail.polarity == 0.0
        assert detail.mood_tags == []
        assert detail.hourglass_pleasantness == 0.0
        assert detail.sentic_concepts == []

    def test_create_with_values(self):
        detail = EmotionDetail(
            polarity=-0.3,
            mood_tags=["frustrated", "anxious"],
            hourglass_pleasantness=-0.5,
            hourglass_attention=-0.2,
            hourglass_sensitivity=0.4,
            hourglass_aptitude=0.1,
            sentic_concepts=["deadline", "pressure"],
        )
        assert detail.polarity == -0.3
        assert len(detail.mood_tags) == 2
        assert detail.hourglass_pleasantness == -0.5


class TestChatResponseExtended:
    def test_response_with_emotion_context(self):
        emotion = EmotionDetail(
            polarity=0.5,
            mood_tags=["happy"],
            hourglass_pleasantness=0.8,
            hourglass_attention=0.3,
            hourglass_sensitivity=-0.1,
            hourglass_aptitude=0.2,
            sentic_concepts=["progress"],
        )
        resp = ChatResponse(
            response="Great progress!",
            used_llm=True,
            emotion_context=emotion,
            ablation_mode=False,
            latency_ms=150.5,
            token_count=8,
        )
        assert resp.emotion_context is not None
        assert resp.emotion_context.polarity == 0.5
        assert resp.ablation_mode is False
        assert resp.latency_ms == 150.5
        assert resp.token_count == 8

    def test_response_ablation_mode(self):
        resp = ChatResponse(
            response="Vanilla response.",
            used_llm=True,
            emotion_context=None,
            ablation_mode=True,
            latency_ms=100.0,
            token_count=5,
        )
        assert resp.emotion_context is None
        assert resp.ablation_mode is True

    def test_backward_compatible(self):
        """Old-style response without new fields still works."""
        resp = ChatResponse(
            response="Hello",
            used_llm=False,
        )
        assert resp.emotion_context is None
        assert resp.ablation_mode is False
        assert resp.latency_ms == 0.0
        assert resp.token_count == 0


class TestAblationConfig:
    def test_default_settings(self):
        from config import get_settings
        settings = get_settings()
        assert settings.ABLATION_MODE is False
        assert settings.EVALUATION_LOGGING is False
        assert settings.EVALUATION_LOG_PATH == "data/evaluation_logs/"

    def test_toggle_ablation(self):
        from config import get_settings
        settings = get_settings()
        original = settings.ABLATION_MODE
        settings.ABLATION_MODE = True
        assert settings.ABLATION_MODE is True
        settings.ABLATION_MODE = original

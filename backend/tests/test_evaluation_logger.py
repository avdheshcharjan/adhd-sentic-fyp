"""Tests for the evaluation logger."""

import os
import tempfile

import pytest
from services.evaluation_logger import EvaluationLogger, EvaluationLogEntry


class TestEvaluationLogEntry:
    def test_create_entry_with_senticnet(self):
        entry = EvaluationLogEntry(
            timestamp="2026-03-19T10:00:00Z",
            conversation_id="conv_001",
            session_id="session_001",
            ablation_mode=False,
            user_message="I can't focus today",
            sentic_polarity=-0.3,
            sentic_mood_tags=["frustrated"],
            hourglass_pleasantness=-0.5,
            hourglass_attention=-0.2,
            hourglass_sensitivity=0.4,
            hourglass_aptitude=0.1,
            llm_response="I hear you, that sounds tough.",
            llm_latency_ms=150.5,
            llm_token_count=12,
        )
        assert entry.ablation_mode is False
        assert entry.sentic_polarity == -0.3
        assert entry.hourglass_pleasantness == -0.5

    def test_create_entry_ablation_mode(self):
        entry = EvaluationLogEntry(
            timestamp="2026-03-19T10:00:00Z",
            conversation_id="conv_002",
            session_id="session_002",
            ablation_mode=True,
            user_message="I can't focus today",
            llm_response="Let me help you with that.",
            llm_latency_ms=120.0,
            llm_token_count=10,
        )
        assert entry.ablation_mode is True
        assert entry.sentic_polarity is None
        assert entry.hourglass_pleasantness is None

    def test_serialization_roundtrip(self):
        entry = EvaluationLogEntry(
            timestamp="2026-03-19T10:00:00Z",
            conversation_id="conv_003",
            session_id="session_003",
            ablation_mode=False,
            user_message="Test",
            sentic_polarity=0.5,
            sentic_mood_tags=["happy"],
            hourglass_pleasantness=0.8,
            hourglass_attention=0.3,
            hourglass_sensitivity=-0.1,
            hourglass_aptitude=0.2,
            llm_response="Great!",
            llm_latency_ms=100.0,
            llm_token_count=5,
        )
        json_str = entry.model_dump_json()
        restored = EvaluationLogEntry.model_validate_json(json_str)
        assert restored.sentic_polarity == 0.5
        assert restored.hourglass_pleasantness == 0.8


class TestEvaluationLogger:
    @pytest.mark.asyncio
    async def test_log_and_load_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EvaluationLogger(log_dir=tmpdir)

            entry1 = EvaluationLogEntry(
                timestamp="2026-03-19T10:00:00Z",
                conversation_id="conv_001",
                session_id="test_session",
                ablation_mode=False,
                user_message="Message 1",
                llm_response="Response 1",
                llm_latency_ms=100.0,
                llm_token_count=5,
            )
            entry2 = EvaluationLogEntry(
                timestamp="2026-03-19T10:01:00Z",
                conversation_id="conv_001",
                session_id="test_session",
                ablation_mode=True,
                user_message="Message 2",
                llm_response="Response 2",
                llm_latency_ms=90.0,
                llm_token_count=6,
            )

            await logger.log(entry1)
            await logger.log(entry2)

            # Verify file exists
            assert os.path.exists(os.path.join(tmpdir, "test_session.jsonl"))

            # Load and verify
            entries = logger.load_session("test_session")
            assert len(entries) == 2
            assert entries[0].user_message == "Message 1"
            assert entries[0].ablation_mode is False
            assert entries[1].user_message == "Message 2"
            assert entries[1].ablation_mode is True

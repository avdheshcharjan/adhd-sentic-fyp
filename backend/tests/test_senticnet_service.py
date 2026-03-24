"""
Phase 1 — Task 1.1: SenticNet Service Smoke Tests.

Tests the SenticNetClient (HTTP API) and SenticNetPipeline (4-tier orchestrator).
These are REAL integration tests — they hit the live SenticNet API.
Requires SENTIC_* API keys in .env.
"""

import asyncio
import random
import time

import pytest
import pytest_asyncio

from services.senticnet_client import SenticNetClient
from services.senticnet_pipeline import SenticNetPipeline
from models.senticnet_result import SenticNetResult, SafetyFlags

random.seed(42)

# ── Fixtures ──────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client():
    c = SenticNetClient()
    yield c
    await c.close()


@pytest_asyncio.fixture
async def pipeline():
    p = SenticNetPipeline()
    yield p
    await p.close()


# ═══════════════════════════════════════════════════════════════════
# Test 1: Basic Concept / Polarity Lookup
# ═══════════════════════════════════════════════════════════════════


class TestBasicConceptLookup:
    """Test individual SenticNet API endpoints."""

    @pytest.mark.asyncio
    async def test_positive_text_polarity(self, client: SenticNetClient):
        """'happy' text should return POSITIVE polarity."""
        result = await client.get_polarity("I am feeling happy and grateful today")
        assert result is not None, "Polarity API returned None — check API key"
        assert "positive" in result.lower(), f"Expected POSITIVE, got: {result}"

    @pytest.mark.asyncio
    async def test_negative_text_polarity(self, client: SenticNetClient):
        """Frustrated text should return NEGATIVE polarity."""
        result = await client.get_polarity("I am so frustrated and annoyed right now")
        assert result is not None, "Polarity API returned None — check API key"
        assert "negative" in result.lower(), f"Expected NEGATIVE, got: {result}"

    @pytest.mark.asyncio
    async def test_emotion_detection(self, client: SenticNetClient):
        """Emotion API should return parseable emotion string."""
        result = await client.get_emotion("I am feeling really overwhelmed and anxious")
        assert result is not None, "Emotion API returned None — check API key"
        # Should be parseable
        parsed = SenticNetClient.parse_emotion_string(result)
        assert parsed["primary"] != "unknown", f"Failed to parse emotion: {result}"
        assert parsed["primary_score"] > 0, f"Expected non-zero score, got: {parsed}"

    @pytest.mark.asyncio
    async def test_intensity_returns_number(self, client: SenticNetClient):
        """Intensity API should return a float."""
        result = await client.get_intensity("I am extremely angry")
        assert result is not None, "Intensity API returned None"
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    @pytest.mark.asyncio
    async def test_depression_returns_percentage(self, client: SenticNetClient):
        """Depression API should return a percentage float."""
        result = await client.get_depression("Everything feels pointless and dark")
        assert result is not None, "Depression API returned None"
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    @pytest.mark.asyncio
    async def test_nonsense_word_handled_gracefully(self, client: SenticNetClient):
        """Nonsense input should return None or a valid response, not crash."""
        result = await client.get_polarity("xyznonword123 blorp zqxjk")
        # May return None or a valid polarity — either is acceptable
        if result is not None:
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_ensemble_returns_dict(self, client: SenticNetClient):
        """Ensemble API should return a dict with all expected fields."""
        result = await client.get_ensemble("I can't focus on my work today")
        assert result is not None, "Ensemble API returned None — check API key"
        assert isinstance(result, dict)
        expected_keys = {"polarity", "intensity", "emotions", "depression", "toxicity"}
        assert expected_keys.issubset(
            set(result.keys())
        ), f"Missing keys. Got: {list(result.keys())}"


# ═══════════════════════════════════════════════════════════════════
# Test 2: Full Text Analysis via Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestFullTextAnalysis:
    """Test the SenticNetPipeline analyze() method."""

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_senticnet_result(self, pipeline: SenticNetPipeline):
        """Full pipeline on real text should return populated SenticNetResult."""
        text = "I'm feeling really overwhelmed with my assignments today"
        start = time.perf_counter()
        result = await pipeline.analyze(text, mode="full")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert isinstance(result, SenticNetResult)
        assert result.mode == "full"
        assert result.text == text

        # Safety tier should be populated
        assert isinstance(result.safety, SafetyFlags)
        assert result.safety.level in ("critical", "high", "moderate", "normal")

        # Emotion should be populated
        assert result.emotion.primary_emotion != "unknown" or result.emotion.polarity != "neutral"

        # ADHD signals should have real scores (may be 0.0 if API returns that)
        assert isinstance(result.adhd_signals.engagement_score, float)
        assert isinstance(result.adhd_signals.wellbeing_score, float)
        assert isinstance(result.adhd_signals.intensity_score, float)

        print(f"\n  Full pipeline latency: {elapsed_ms:.0f}ms")
        print(f"  Emotion: {result.emotion.primary_emotion}")
        print(f"  Safety level: {result.safety.level}")
        print(f"  Engagement: {result.adhd_signals.engagement_score}")
        print(f"  Wellbeing: {result.adhd_signals.wellbeing_score}")

        # Latency should be reasonable (< 30s for 4 tiers hitting external API)
        assert elapsed_ms < 30_000, f"Pipeline took {elapsed_ms:.0f}ms — too slow"

    @pytest.mark.asyncio
    async def test_lightweight_pipeline(self, pipeline: SenticNetPipeline):
        """Lightweight mode should return emotion + engagement + intensity."""
        text = "I'm bored and can't concentrate"
        start = time.perf_counter()
        result = await pipeline.analyze(text, mode="lightweight")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.mode == "lightweight"
        assert isinstance(result.adhd_signals.engagement_score, float)
        assert isinstance(result.adhd_signals.intensity_score, float)

        print(f"\n  Lightweight pipeline latency: {elapsed_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_safety_only_pipeline(self, pipeline: SenticNetPipeline):
        """Safety-only mode should return safety flags quickly."""
        text = "I feel really hopeless about everything"
        start = time.perf_counter()
        result = await pipeline.analyze(text, mode="safety_only")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result.mode == "safety_only"
        assert isinstance(result.safety.depression_score, float)
        assert isinstance(result.safety.toxicity_score, float)
        assert isinstance(result.safety.intensity_score, float)
        assert result.safety.level in ("critical", "high", "moderate", "normal")

        print(f"\n  Safety-only pipeline latency: {elapsed_ms:.0f}ms")
        print(f"  Depression: {result.safety.depression_score}")
        print(f"  Toxicity: {result.safety.toxicity_score}")
        print(f"  Level: {result.safety.level}")


# ═══════════════════════════════════════════════════════════════════
# Test 3: Empty/Edge Case Handling
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases that must not crash."""

    @pytest.mark.asyncio
    async def test_empty_string(self, client: SenticNetClient):
        """Empty string should not crash."""
        result = await client.get_polarity("")
        # sanitize("") returns "", _call_api returns None for empty
        assert result is None

    @pytest.mark.asyncio
    async def test_emoji_only(self, client: SenticNetClient):
        """Emoji-only input should not crash."""
        result = await client.get_polarity("😀🎉")
        # May return None or a response — either is fine
        if result is not None:
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_very_long_string(self, client: SenticNetClient):
        """5000-char input should not hang (truncated to 8000 internally)."""
        long_text = "I feel very anxious about my work. " * 150  # ~5250 chars
        start = time.perf_counter()
        result = await client.get_polarity(long_text)
        elapsed = time.perf_counter() - start

        # Should complete within timeout (30s default)
        assert elapsed < 35, f"Long text took {elapsed:.1f}s — too slow"

    @pytest.mark.asyncio
    async def test_illegal_characters_stripped(self, client: SenticNetClient):
        """Text with illegal chars (& # ; { }) should be sanitized."""
        sanitized = SenticNetClient.sanitize("I feel {angry} & #frustrated;")
        assert "&" not in sanitized
        assert "#" not in sanitized
        assert ";" not in sanitized
        assert "{" not in sanitized
        assert "}" not in sanitized

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_text(self, pipeline: SenticNetPipeline):
        """Pipeline should handle empty text gracefully."""
        result = await pipeline.analyze("", mode="full")
        assert isinstance(result, SenticNetResult)
        # Safety should still have defaults
        assert result.safety.level in ("critical", "high", "moderate", "normal")


# ═══════════════════════════════════════════════════════════════════
# Test 4: API Resilience (mocked failures)
# ═══════════════════════════════════════════════════════════════════


class TestAPIResilience:
    """Test graceful handling of API failures."""

    @pytest.mark.asyncio
    async def test_server_error_returns_none(self, client: SenticNetClient):
        """Mock 500 response → client should return None, not crash."""
        import httpx
        from unittest.mock import AsyncMock, patch

        mock_response = httpx.Response(
            status_code=500,
            request=httpx.Request("GET", "https://sentic.net/api/en/test.py"),
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=mock_response.request, response=mock_response
        )
        mock_client.is_closed = False

        client._client = mock_client
        result = await client.get_polarity("test text")
        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self, client: SenticNetClient):
        """Mock network timeout → client should return None within timeout."""
        import httpx
        from unittest.mock import AsyncMock

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.is_closed = False

        client._client = mock_client

        start = time.perf_counter()
        result = await client.get_polarity("test text")
        elapsed = time.perf_counter() - start

        assert result is None
        # Should not take long since we mocked the timeout
        assert elapsed < 5, f"Timeout handling took {elapsed:.1f}s"

    @pytest.mark.asyncio
    async def test_pipeline_resilient_to_api_failure(self):
        """Pipeline should still return a result even if individual APIs fail."""
        from unittest.mock import AsyncMock

        pipeline = SenticNetPipeline()
        # Mock the client to return None for everything
        pipeline.client = AsyncMock()
        pipeline.client.get_depression.return_value = None
        pipeline.client.get_toxicity.return_value = None
        pipeline.client.get_intensity.return_value = None
        pipeline.client.get_emotion.return_value = None
        pipeline.client.get_polarity.return_value = None
        pipeline.client.get_subjectivity.return_value = None
        pipeline.client.get_sarcasm.return_value = None
        pipeline.client.get_engagement.return_value = None
        pipeline.client.get_wellbeing.return_value = None
        pipeline.client.get_concepts.return_value = None
        pipeline.client.get_aspects.return_value = None
        pipeline.client.get_personality.return_value = None
        pipeline.client.get_ensemble.return_value = None

        result = await pipeline.analyze("test text", mode="full")

        # Should still return a valid result with defaults
        assert isinstance(result, SenticNetResult)
        assert result.safety.level == "normal"  # defaults
        assert result.emotion.primary_emotion == "unknown"


# ═══════════════════════════════════════════════════════════════════
# Test 5: Hourglass → ADHD State Mapping
# ═══════════════════════════════════════════════════════════════════


class TestHourglassMapping:
    """Test the Hourglass of Emotions → ADHD state mapping."""

    def test_frustration_spiral(self):
        pipeline = SenticNetPipeline()
        result = pipeline.map_hourglass_to_adhd_state({
            "introspection": -0.5,
            "temper": -0.6,
            "attitude": 0.0,
            "sensitivity": 0.0,
        })
        assert result["primary_adhd_state"] == "frustration_spiral"
        assert result["recommended_ef_domain"] == "self_regulation_emotion"

    def test_productive_flow(self):
        pipeline = SenticNetPipeline()
        result = pipeline.map_hourglass_to_adhd_state({
            "introspection": 0.5,
            "temper": 0.3,
            "attitude": 0.4,
            "sensitivity": 0.6,
        })
        assert result["primary_adhd_state"] == "productive_flow"
        assert result["recommended_ef_domain"] == "none"

    def test_boredom_disengagement(self):
        pipeline = SenticNetPipeline()
        result = pipeline.map_hourglass_to_adhd_state({
            "introspection": -0.5,
            "temper": 0.0,
            "attitude": 0.0,
            "sensitivity": -0.4,
        })
        assert result["primary_adhd_state"] == "boredom_disengagement"
        assert result["recommended_ef_domain"] == "self_motivation"

    def test_neutral_state(self):
        pipeline = SenticNetPipeline()
        result = pipeline.map_hourglass_to_adhd_state({
            "introspection": 0.0,
            "temper": 0.0,
            "attitude": 0.0,
            "sensitivity": 0.0,
        })
        assert result["primary_adhd_state"] == "neutral"


# ═══════════════════════════════════════════════════════════════════
# Test 6: Parser Unit Tests
# ═══════════════════════════════════════════════════════════════════


class TestParsers:
    """Test the static parser methods."""

    def test_parse_emotion_string(self):
        parsed = SenticNetClient.parse_emotion_string("fear (99.7%) & annoyance (50.0%)")
        assert parsed["primary"] == "fear"
        assert parsed["primary_score"] == 99.7
        assert parsed["secondary"] == "annoyance"
        assert parsed["secondary_score"] == 50.0

    def test_parse_emotion_no_emotions(self):
        parsed = SenticNetClient.parse_emotion_string("No emotions detected")
        assert parsed["primary"] == "unknown"

    def test_parse_personality_string(self):
        parsed = SenticNetClient.parse_personality_string("ENTJ (O↑C↑E↑A↓N↓)")
        assert parsed["mbti"] == "ENTJ"
        assert parsed["O"] == "↑"
        assert parsed["A"] == "↓"

    def test_parse_percentage(self):
        assert SenticNetClient._parse_percentage("33.33%") == 33.33
        assert SenticNetClient._parse_percentage("-50.0%") == -50.0
        assert SenticNetClient._parse_percentage(None) is None

    def test_parse_number(self):
        assert SenticNetClient._parse_number("41") == 41.0
        assert SenticNetClient._parse_number("-16.5") == -16.5
        assert SenticNetClient._parse_number(None) is None

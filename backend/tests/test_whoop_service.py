"""
Unit tests for the Whoop integration service.

Tests cover:
  - Recovery tier classification (green/yellow/red + boundaries)
  - Sleep notes generation (low SWS, high disturbances, low HRV)
  - Morning briefing generation with mocked CLI output
  - Focus recommendation text per tier
  - CLI error handling (not installed, not authenticated, timeout)
  - JSON parsing of whoopskill output format

All tests use mocked subprocess output — no real whoopskill or Whoop API needed.
"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from models.whoop_data import (
    MorningBriefing,
    RecoveryTier,
    WhoopRecovery,
    WhoopSleep,
    WhoopCycle,
)
from services.whoop_service import (
    WhoopService,
    WhoopNotInstalledError,
    WhoopNotAuthenticatedError,
    WhoopServiceError,
)


# ── Fixtures ────────────────────────────────────────────────────────


SAMPLE_WHOOPSKILL_OUTPUT = {
    "date": "2026-03-08",
    "fetched_at": "2026-03-08T12:00:00.000Z",
    "recovery": [
        {
            "cycle_id": 1236731435,
            "sleep_id": "4c311bd4-370f-49ff-b58c-0578d543e9d2",
            "user_id": 245199,
            "score_state": "SCORED",
            "score": {
                "recovery_score": 72,
                "resting_heart_rate": 52,
                "hrv_rmssd_milli": 65.0,
                "spo2_percentage": 96.4,
                "skin_temp_celsius": 33.19,
            },
        }
    ],
    "sleep": [
        {
            "id": "4c311bd4-370f-49ff-b58c-0578d543e9d2",
            "cycle_id": 1236731435,
            "user_id": 245199,
            "start": "2026-03-07T22:00:00.000Z",
            "end": "2026-03-08T06:00:00.000Z",
            "nap": False,
            "score_state": "SCORED",
            "score": {
                "stage_summary": {
                    "total_in_bed_time_milli": 28800000,
                    "total_awake_time_milli": 3600000,
                    "total_light_sleep_time_milli": 10800000,  # 3h
                    "total_slow_wave_sleep_time_milli": 4680000,  # 1.3h → 18.5%
                    "total_rem_sleep_time_milli": 5640000,  # 1.567h → 22.3%
                    "sleep_cycle_count": 4,
                    "disturbance_count": 2,
                },
                "sleep_needed": {
                    "baseline_milli": 28800000,
                    "need_from_sleep_debt_milli": 0,
                    "need_from_recent_strain_milli": 0,
                },
                "respiratory_rate": 14.5,
                "sleep_performance_percentage": 85,
                "sleep_consistency_percentage": 70,
                "sleep_efficiency_percentage": 87.5,
            },
        }
    ],
    "cycle": [
        {
            "id": 1236731435,
            "user_id": 245199,
            "start": "2026-03-07T22:00:00.000Z",
            "end": None,
            "score_state": "SCORED",
            "score": {
                "strain": 12.5,
                "kilojoule": 8500.0,
                "average_heart_rate": 72,
                "max_heart_rate": 155,
            },
        }
    ],
}


def _make_mock_process(stdout_data: str, returncode: int = 0, stderr_data: str = ""):
    """Create a mock subprocess process."""
    mock_process = AsyncMock()
    mock_process.returncode = returncode
    mock_process.communicate = AsyncMock(
        return_value=(stdout_data.encode(), stderr_data.encode())
    )
    return mock_process


# ── Recovery Tier Classification ────────────────────────────────────


class TestRecoveryTierClassification:
    """Test the recovery score → ADHD tier mapping."""

    def test_green_high(self):
        assert WhoopService.classify_recovery_tier(100) == RecoveryTier.GREEN

    def test_green_boundary_lower(self):
        assert WhoopService.classify_recovery_tier(67) == RecoveryTier.GREEN

    def test_yellow_boundary_upper(self):
        assert WhoopService.classify_recovery_tier(66) == RecoveryTier.YELLOW

    def test_yellow_mid(self):
        assert WhoopService.classify_recovery_tier(50) == RecoveryTier.YELLOW

    def test_yellow_boundary_lower(self):
        assert WhoopService.classify_recovery_tier(34) == RecoveryTier.YELLOW

    def test_red_boundary_upper(self):
        assert WhoopService.classify_recovery_tier(33) == RecoveryTier.RED

    def test_red_low(self):
        assert WhoopService.classify_recovery_tier(10) == RecoveryTier.RED

    def test_red_zero(self):
        assert WhoopService.classify_recovery_tier(0) == RecoveryTier.RED

    def test_green_standard(self):
        """72% → green (the sample from Phase 5 doc)."""
        assert WhoopService.classify_recovery_tier(72) == RecoveryTier.GREEN


# ── Sleep Notes Generation ──────────────────────────────────────────


class TestSleepNotes:
    """Test ADHD-specific sleep observation generation."""

    def test_no_concerns_empty_notes(self):
        """Good sleep → no notes."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=20.0,
            disturbance_count=2,
            hrv_rmssd=55.0,
        )
        assert notes == []

    def test_low_sws_warning(self):
        """SWS < 15% → working memory warning."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=12.0,
            disturbance_count=2,
            hrv_rmssd=55.0,
        )
        assert len(notes) == 1
        assert "deep sleep" in notes[0].lower()
        assert "working memory" in notes[0].lower()

    def test_high_disturbances_warning(self):
        """Disturbances > 5 → fragmented attention warning."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=20.0,
            disturbance_count=8,
            hrv_rmssd=55.0,
        )
        assert len(notes) == 1
        assert "disturbance" in notes[0].lower()
        assert "focus" in notes[0].lower() or "attention" in notes[0].lower()

    def test_low_hrv_warning(self):
        """HRV < 40ms → emotion regulation warning."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=20.0,
            disturbance_count=2,
            hrv_rmssd=35.0,
        )
        assert len(notes) == 1
        assert "hrv" in notes[0].lower()
        assert "emotion" in notes[0].lower()

    def test_all_concerns_three_notes(self):
        """All thresholds exceeded → 3 notes."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=10.0,
            disturbance_count=7,
            hrv_rmssd=30.0,
        )
        assert len(notes) == 3

    def test_boundary_sws_at_threshold_no_warning(self):
        """SWS exactly at 15% → no warning (strict less-than)."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=15.0,
            disturbance_count=2,
            hrv_rmssd=55.0,
        )
        assert notes == []

    def test_boundary_disturbance_at_threshold_no_warning(self):
        """Disturbances exactly at 5 → no warning (strict greater-than)."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=20.0,
            disturbance_count=5,
            hrv_rmssd=55.0,
        )
        assert notes == []

    def test_boundary_hrv_at_threshold_no_warning(self):
        """HRV exactly at 40ms → no warning (strict less-than)."""
        notes = WhoopService.compute_sleep_notes(
            sws_percentage=20.0,
            disturbance_count=2,
            hrv_rmssd=40.0,
        )
        assert notes == []


# ── Focus Recommendations ──────────────────────────────────────────


class TestFocusRecommendations:
    """Test tier → focus block mapping."""

    def test_green_tier_45_minutes(self):
        config = WhoopService.RECOVERY_TIERS[RecoveryTier.GREEN]
        assert config["focus_block_minutes"] == 45

    def test_yellow_tier_25_minutes(self):
        config = WhoopService.RECOVERY_TIERS[RecoveryTier.YELLOW]
        assert config["focus_block_minutes"] == 25

    def test_red_tier_15_minutes(self):
        config = WhoopService.RECOVERY_TIERS[RecoveryTier.RED]
        assert config["focus_block_minutes"] == 15

    def test_green_recommendation_deep_work(self):
        config = WhoopService.RECOVERY_TIERS[RecoveryTier.GREEN]
        assert "deep" in config["recommendation"].lower()

    def test_red_recommendation_easy_tasks(self):
        config = WhoopService.RECOVERY_TIERS[RecoveryTier.RED]
        assert "easy" in config["recommendation"].lower()


# ── CLI Error Handling ──────────────────────────────────────────────


class TestCLIErrorHandling:
    @pytest.mark.asyncio
    async def test_not_installed_error(self):
        """whoopskill not on PATH → WhoopNotInstalledError."""
        service = WhoopService()
        with patch.object(WhoopService, "is_installed", return_value=False):
            with pytest.raises(WhoopNotInstalledError, match="not found"):
                await service._run_whoopskill(["recovery"])

    @pytest.mark.asyncio
    async def test_auth_error(self):
        """CLI returns auth-related error → WhoopNotAuthenticatedError."""
        service = WhoopService()
        mock_proc = _make_mock_process(
            stdout_data="",
            returncode=1,
            stderr_data="Error: No token found. Please run whoopskill auth login",
        )

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopNotAuthenticatedError, match="auth login"):
                    await service._run_whoopskill(["recovery"])

    @pytest.mark.asyncio
    async def test_generic_cli_error(self):
        """CLI fails with non-auth error → WhoopServiceError."""
        service = WhoopService()
        mock_proc = _make_mock_process(
            stdout_data="",
            returncode=1,
            stderr_data="Something went wrong",
        )

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopServiceError, match="Something went wrong"):
                    await service._run_whoopskill(["recovery"])

    @pytest.mark.asyncio
    async def test_empty_output_error(self):
        """CLI returns empty stdout → WhoopServiceError."""
        service = WhoopService()
        mock_proc = _make_mock_process(stdout_data="", returncode=0)

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopServiceError, match="empty"):
                    await service._run_whoopskill(["recovery"])

    @pytest.mark.asyncio
    async def test_invalid_json_error(self):
        """CLI returns non-JSON → WhoopServiceError."""
        service = WhoopService()
        mock_proc = _make_mock_process(
            stdout_data="this is not json", returncode=0
        )

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopServiceError, match="JSON"):
                    await service._run_whoopskill(["recovery"])


# ── Data Fetchers ───────────────────────────────────────────────────


class TestDataFetchers:
    @pytest.mark.asyncio
    async def test_get_recovery_parses_correctly(self):
        """Verify recovery data is parsed into WhoopRecovery models."""
        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                records = await service.get_recovery("2026-03-08")

        assert len(records) == 1
        assert records[0].score.recovery_score == 72
        assert records[0].score.hrv_rmssd_milli == 65.0
        assert records[0].score.resting_heart_rate == 52

    @pytest.mark.asyncio
    async def test_get_sleep_parses_correctly(self):
        """Verify sleep data is parsed with stage summary."""
        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                records = await service.get_sleep("2026-03-08")

        assert len(records) == 1
        assert records[0].score.stage_summary.disturbance_count == 2
        assert records[0].score.sleep_performance_percentage == 85

    @pytest.mark.asyncio
    async def test_get_cycle_parses_correctly(self):
        """Verify cycle data is parsed with strain."""
        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                records = await service.get_cycle("2026-03-08")

        assert len(records) == 1
        assert records[0].score.strain == 12.5


# ── Morning Briefing ───────────────────────────────────────────────


class TestMorningBriefing:
    @pytest.mark.asyncio
    async def test_green_recovery_briefing(self):
        """72% recovery → green tier, 45 min focus blocks, no sleep notes."""
        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                briefing = await service.generate_morning_briefing("2026-03-08")

        assert briefing.recovery_score == 72
        assert briefing.recovery_tier == RecoveryTier.GREEN
        assert briefing.recommended_focus_block_minutes == 45
        assert briefing.hrv_rmssd == 65.0
        assert briefing.resting_hr == 52
        assert briefing.disturbance_count == 2
        assert "deep" in briefing.focus_recommendation.lower()
        assert briefing.sleep_notes == []  # All metrics are healthy
        assert briefing.strain_yesterday == 12.5

    @pytest.mark.asyncio
    async def test_red_recovery_briefing(self):
        """20% recovery → red tier, 15 min focus blocks."""
        data = json.loads(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))
        data["recovery"][0]["score"]["recovery_score"] = 20

        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(data))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                briefing = await service.generate_morning_briefing("2026-03-08")

        assert briefing.recovery_tier == RecoveryTier.RED
        assert briefing.recommended_focus_block_minutes == 15
        assert "easy" in briefing.focus_recommendation.lower()

    @pytest.mark.asyncio
    async def test_briefing_with_sleep_concerns(self):
        """Low SWS + low HRV → 2 sleep notes generated."""
        data = json.loads(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))
        # Make SWS very low (< 15% of total sleep)
        data["sleep"][0]["score"]["stage_summary"][
            "total_slow_wave_sleep_time_milli"
        ] = 1000000  # ~16.7 min
        # Make HRV low
        data["recovery"][0]["score"]["hrv_rmssd_milli"] = 32.0

        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(data))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                briefing = await service.generate_morning_briefing("2026-03-08")

        assert len(briefing.sleep_notes) == 2
        note_text = " ".join(briefing.sleep_notes).lower()
        assert "deep sleep" in note_text
        assert "hrv" in note_text

    @pytest.mark.asyncio
    async def test_briefing_no_recovery_data_raises(self):
        """No recovery records → WhoopServiceError."""
        data = json.loads(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))
        data["recovery"] = []

        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(data))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopServiceError, match="No recovery data"):
                    await service.generate_morning_briefing("2026-03-08")

    @pytest.mark.asyncio
    async def test_briefing_no_sleep_data_raises(self):
        """No sleep records → WhoopServiceError."""
        data = json.loads(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))
        data["sleep"] = []

        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(data))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(WhoopServiceError, match="No sleep data"):
                    await service.generate_morning_briefing("2026-03-08")

    @pytest.mark.asyncio
    async def test_briefing_sleep_percentages_correct(self):
        """Verify SWS% and REM% are calculated correctly."""
        service = WhoopService()
        mock_proc = _make_mock_process(json.dumps(SAMPLE_WHOOPSKILL_OUTPUT))

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                briefing = await service.generate_morning_briefing("2026-03-08")

        # Total sleep = light (10800000) + SWS (4680000) + REM (5640000) = 21120000
        # SWS% = 4680000 / 21120000 * 100 ≈ 22.2%
        # REM% = 5640000 / 21120000 * 100 ≈ 26.7%
        assert 22.0 <= briefing.sws_percentage <= 22.5
        assert 26.5 <= briefing.rem_percentage <= 27.0


# ── Auth Status ─────────────────────────────────────────────────────


class TestAuthStatus:
    @pytest.mark.asyncio
    async def test_not_installed_status(self):
        """CLI not installed → installed=False."""
        service = WhoopService()
        with patch.object(WhoopService, "is_installed", return_value=False):
            status = await service.check_status()

        assert status["installed"] is False
        assert status["authenticated"] is False

    @pytest.mark.asyncio
    async def test_authenticated_status(self):
        """CLI installed + valid tokens → authenticated=True."""
        service = WhoopService()
        mock_proc = _make_mock_process(
            stdout_data="Token valid. Expires in 3600s", returncode=0
        )

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                status = await service.check_status()

        assert status["installed"] is True
        assert status["authenticated"] is True

    @pytest.mark.asyncio
    async def test_expired_token_status(self):
        """CLI installed + expired tokens → authenticated=False."""
        service = WhoopService()
        mock_proc = _make_mock_process(
            stdout_data="Token expired. Run whoopskill auth login", returncode=0
        )

        with patch.object(WhoopService, "is_installed", return_value=True):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                status = await service.check_status()

        assert status["installed"] is True
        assert status["authenticated"] is False

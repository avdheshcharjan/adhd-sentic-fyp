"""Whoop integration service — wraps the whoopskill CLI.

Instead of implementing custom OAuth 2.0, we delegate to the whoopskill CLI
(https://github.com/koala73/whoopskill) which handles authentication, token
storage (~/.whoop-cli/tokens.json), and auto-refresh.

The backend calls `whoopskill` via async subprocess and parses its JSON output.

Prerequisites:
    1. npm install -g whoopskill
    2. whoopskill auth login   (one-time browser-based OAuth)
"""

import asyncio
import json
import logging
import shutil
from datetime import date
from typing import Any, Optional

from models.whoop_data import (
    MorningBriefing,
    RecoveryTier,
    WhoopCycle,
    WhoopRecovery,
    WhoopSleep,
)

logger = logging.getLogger("adhd-brain.whoop")


class WhoopServiceError(Exception):
    """Base exception for Whoop service errors."""

    pass


class WhoopNotInstalledError(WhoopServiceError):
    """whoopskill CLI is not installed."""

    pass


class WhoopNotAuthenticatedError(WhoopServiceError):
    """whoopskill CLI is not authenticated."""

    pass


class WhoopService:
    """Service that wraps the whoopskill CLI to fetch Whoop data.

    Usage:
        service = WhoopService()
        briefing = await service.generate_morning_briefing()
    """

    WHOOPSKILL_CMD = "whoopskill"

    # ── Recovery-to-ADHD Mapping Tables ─────────────────────────────

    RECOVERY_TIERS = {
        RecoveryTier.GREEN: {
            "range": (67, 100),
            "focus_block_minutes": 45,
            "recommendation": (
                "Great recovery — today is optimal for deep, challenging work."
            ),
        },
        RecoveryTier.YELLOW: {
            "range": (34, 66),
            "focus_block_minutes": 25,
            "recommendation": (
                "Moderate recovery — use structured pacing with extra scaffolding."
            ),
        },
        RecoveryTier.RED: {
            "range": (0, 33),
            "focus_block_minutes": 15,
            "recommendation": (
                "Low recovery — stick to easy tasks, frequent breaks, "
                "and written lists."
            ),
        },
    }

    # Sleep-to-ADHD thresholds from Phase 5 doc
    SWS_LOW_THRESHOLD = 15.0  # % — below this → working memory issues
    DISTURBANCE_HIGH_THRESHOLD = 5  # count — above this → fragmented attention
    HRV_LOW_THRESHOLD = 40.0  # ms — below this → emotion regulation harder

    # ── Core CLI wrapper ────────────────────────────────────────────

    @staticmethod
    def is_installed() -> bool:
        """Check if whoopskill CLI is available on PATH."""
        return shutil.which("whoopskill") is not None

    async def _run_whoopskill(self, args: list[str]) -> dict[str, Any]:
        """Execute whoopskill CLI and parse JSON output.

        Args:
            args: CLI arguments (e.g. ["recovery", "--date", "2026-03-08"])

        Returns:
            Parsed JSON dict from whoopskill stdout.

        Raises:
            WhoopNotInstalledError: If whoopskill is not on PATH.
            WhoopNotAuthenticatedError: If tokens are expired or missing.
            WhoopServiceError: For other CLI errors.
        """
        if not self.is_installed():
            raise WhoopNotInstalledError(
                "whoopskill CLI not found. Install with: npm install -g whoopskill"
            )

        cmd = [self.WHOOPSKILL_CMD] + args
        logger.debug(f"Running: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30.0
            )
        except asyncio.TimeoutError:
            raise WhoopServiceError("whoopskill CLI timed out after 30s")
        except FileNotFoundError:
            raise WhoopNotInstalledError(
                "whoopskill CLI not found. Install with: npm install -g whoopskill"
            )

        stdout_text = stdout.decode("utf-8").strip()
        stderr_text = stderr.decode("utf-8").strip()

        if process.returncode != 0:
            # Check for authentication errors
            error_lower = (stderr_text + stdout_text).lower()
            if any(
                kw in error_lower
                for kw in ["auth", "token", "unauthorized", "login"]
            ):
                raise WhoopNotAuthenticatedError(
                    "Whoop not authenticated. Run: whoopskill auth login"
                )
            raise WhoopServiceError(
                f"whoopskill CLI failed (exit {process.returncode}): "
                f"{stderr_text or stdout_text}"
            )

        if not stdout_text:
            raise WhoopServiceError("whoopskill returned empty output")

        try:
            return json.loads(stdout_text)
        except json.JSONDecodeError as e:
            raise WhoopServiceError(
                f"Failed to parse whoopskill output as JSON: {e}"
            )

    # ── Status / Auth ───────────────────────────────────────────────

    async def check_status(self) -> dict[str, Any]:
        """Check whoopskill authentication status.

        Returns:
            Dict with 'installed', 'authenticated', and 'message' keys.
        """
        if not self.is_installed():
            return {
                "installed": False,
                "authenticated": False,
                "message": (
                    "whoopskill CLI not found. "
                    "Install with: npm install -g whoopskill"
                ),
            }

        try:
            process = await asyncio.create_subprocess_exec(
                self.WHOOPSKILL_CMD, "auth", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=10.0
            )
            output = stdout.decode("utf-8").strip()
            is_auth = process.returncode == 0 and "expired" not in output.lower()

            return {
                "installed": True,
                "authenticated": is_auth,
                "message": output or stderr.decode("utf-8").strip(),
            }
        except Exception as e:
            return {
                "installed": True,
                "authenticated": False,
                "message": f"Error checking status: {e}",
            }

    async def logout(self) -> None:
        """Run `whoopskill auth logout` to clear stored tokens."""
        if not self.is_installed():
            raise WhoopNotInstalledError(
                "whoopskill CLI not found. Install with: npm install -g whoopskill"
            )

        try:
            process = await asyncio.create_subprocess_exec(
                self.WHOOPSKILL_CMD, "auth", "logout",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=10.0)
            logger.info("Whoop logout completed")
        except Exception as e:
            logger.error(f"Whoop logout failed: {e}")
            raise WhoopServiceError(f"Failed to logout: {e}")

    # ── Data fetchers ───────────────────────────────────────────────

    async def get_recovery(
        self, target_date: Optional[str] = None
    ) -> list[WhoopRecovery]:
        """Fetch recovery data for a given date.

        Args:
            target_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of WhoopRecovery records (usually 1 per day).
        """
        args = ["recovery"]
        if target_date:
            args.extend(["--date", target_date])

        data = await self._run_whoopskill(args)
        raw_records = data.get("recovery", [])
        return [WhoopRecovery(**r) for r in raw_records]

    async def get_sleep(
        self, target_date: Optional[str] = None
    ) -> list[WhoopSleep]:
        """Fetch sleep data for a given date.

        Args:
            target_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of WhoopSleep records.
        """
        args = ["sleep"]
        if target_date:
            args.extend(["--date", target_date])

        data = await self._run_whoopskill(args)
        raw_records = data.get("sleep", [])
        return [WhoopSleep(**r) for r in raw_records]

    async def get_cycle(
        self, target_date: Optional[str] = None
    ) -> list[WhoopCycle]:
        """Fetch cycle/strain data for a given date.

        Args:
            target_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of WhoopCycle records.
        """
        args = ["cycle"]
        if target_date:
            args.extend(["--date", target_date])

        data = await self._run_whoopskill(args)
        raw_records = data.get("cycle", [])
        return [WhoopCycle(**r) for r in raw_records]

    async def get_all_data(
        self, target_date: Optional[str] = None
    ) -> dict[str, Any]:
        """Fetch all data types for a given date.

        Args:
            target_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Raw whoopskill JSON dict with all data types.
        """
        args = ["--sleep", "--recovery", "--cycle"]
        if target_date:
            args.extend(["--date", target_date])

        return await self._run_whoopskill(args)

    # ── Recovery tier classification ────────────────────────────────

    @staticmethod
    def classify_recovery_tier(score: int) -> RecoveryTier:
        """Map Whoop recovery score (0-100) to ADHD recovery tier.

        Green  (67-100): Optimal executive function
        Yellow (34-66):  Moderate — needs structured pacing
        Red    (0-33):   Impaired — easy tasks, frequent breaks

        Args:
            score: Recovery score 0-100.

        Returns:
            RecoveryTier enum value.
        """
        if score >= 67:
            return RecoveryTier.GREEN
        elif score >= 34:
            return RecoveryTier.YELLOW
        else:
            return RecoveryTier.RED

    # ── Sleep notes (ADHD-specific) ─────────────────────────────────

    @classmethod
    def compute_sleep_notes(
        cls,
        sws_percentage: float,
        disturbance_count: int,
        hrv_rmssd: float,
    ) -> list[str]:
        """Generate ADHD-specific sleep observations.

        Based on sleep-to-ADHD mapping from Phase 5 specification:
        - Low SWS (<15%): Working memory issues
        - High disturbances (>5): Fragmented attention
        - Low HRV (<40ms): Emotion regulation harder

        Args:
            sws_percentage: Slow-wave sleep as % of total sleep.
            disturbance_count: Number of sleep disturbances.
            hrv_rmssd: Heart rate variability in milliseconds.

        Returns:
            List of observation strings.
        """
        notes = []

        if sws_percentage < cls.SWS_LOW_THRESHOLD:
            notes.append(
                f"Low deep sleep ({sws_percentage:.1f}%) — working memory "
                f"may be reduced. Use written over verbal instructions."
            )

        if disturbance_count > cls.DISTURBANCE_HIGH_THRESHOLD:
            notes.append(
                f"High sleep disturbances ({disturbance_count}) — attention "
                f"may be fragmented. Use shorter focus blocks."
            )

        if hrv_rmssd < cls.HRV_LOW_THRESHOLD:
            notes.append(
                f"Low HRV ({hrv_rmssd:.1f}ms) — emotion regulation may be "
                f"harder today. Allow extra grace and grounding exercises."
            )

        return notes

    # ── Morning Briefing ────────────────────────────────────────────

    async def generate_morning_briefing(
        self, target_date: Optional[str] = None
    ) -> MorningBriefing:
        """Generate an ADHD-tailored morning briefing from Whoop data.

        Fetches recovery + sleep + cycle data, applies ADHD mapping tables,
        and returns a structured briefing with focus recommendations.

        Args:
            target_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            MorningBriefing with recovery tier, focus recommendations,
            and sleep notes.

        Raises:
            WhoopServiceError: If data fetch fails or data is insufficient.
        """
        briefing_date = target_date or date.today().isoformat()

        # Fetch all data in one CLI call
        raw = await self.get_all_data(briefing_date)

        # Parse recovery
        recovery_records = raw.get("recovery", [])
        if not recovery_records:
            raise WhoopServiceError(
                f"No recovery data available for {briefing_date}"
            )

        recovery = WhoopRecovery(**recovery_records[0])
        recovery_score = recovery.score.recovery_score
        recovery_tier = self.classify_recovery_tier(recovery_score)
        hrv_rmssd = recovery.score.hrv_rmssd_milli
        resting_hr = recovery.score.resting_heart_rate

        # Parse sleep
        sleep_records = raw.get("sleep", [])
        if not sleep_records:
            raise WhoopServiceError(
                f"No sleep data available for {briefing_date}"
            )

        sleep = WhoopSleep(**sleep_records[0])
        stages = sleep.score.stage_summary

        # Calculate sleep stage percentages
        total_sleep_milli = (
            stages.total_light_sleep_time_milli
            + stages.total_slow_wave_sleep_time_milli
            + stages.total_rem_sleep_time_milli
        )
        total_sleep_milli = max(total_sleep_milli, 1)  # avoid division by zero

        sws_pct = (stages.total_slow_wave_sleep_time_milli / total_sleep_milli) * 100
        rem_pct = (stages.total_rem_sleep_time_milli / total_sleep_milli) * 100

        # Parse cycle / strain
        cycle_records = raw.get("cycle", [])
        strain_yesterday = None
        if cycle_records:
            cycle = WhoopCycle(**cycle_records[0])
            strain_yesterday = cycle.score.strain

        # Generate ADHD-specific recommendations
        tier_config = self.RECOVERY_TIERS[recovery_tier]
        sleep_notes = self.compute_sleep_notes(
            sws_percentage=sws_pct,
            disturbance_count=stages.disturbance_count,
            hrv_rmssd=hrv_rmssd,
        )

        return MorningBriefing(
            date=briefing_date,
            recovery_score=recovery_score,
            recovery_tier=recovery_tier,
            hrv_rmssd=hrv_rmssd,
            resting_hr=resting_hr,
            sleep_performance=sleep.score.sleep_performance_percentage,
            sws_percentage=round(sws_pct, 1),
            rem_percentage=round(rem_pct, 1),
            disturbance_count=stages.disturbance_count,
            focus_recommendation=tier_config["recommendation"],
            recommended_focus_block_minutes=tier_config["focus_block_minutes"],
            sleep_notes=sleep_notes,
            strain_yesterday=strain_yesterday,
        )

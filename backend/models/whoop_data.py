"""Pydantic models for Whoop physiological data.

Parses JSON output from the whoopskill CLI (koala73/whoopskill).
Models map directly to Whoop API v2 response structures.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Recovery ────────────────────────────────────────────────────────


class RecoveryTier(str, Enum):
    """Recovery-to-ADHD executive function mapping.

    Green  (67-100%): Optimal EF — 45 min focus blocks, deep challenging work
    Yellow (34-66%):  Moderate EF — 25 min blocks, structured pacing
    Red    (0-33%):   Impaired EF — 15 min blocks, easy tasks, frequent breaks
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class WhoopRecoveryScore(BaseModel):
    """Score payload from whoopskill recovery output."""

    recovery_score: int = Field(ge=0, le=100)
    resting_heart_rate: float
    hrv_rmssd_milli: float  # HRV in milliseconds
    spo2_percentage: Optional[float] = None
    skin_temp_celsius: Optional[float] = None


class WhoopRecovery(BaseModel):
    """Single recovery record from whoopskill."""

    cycle_id: int
    sleep_id: Optional[str] = None
    user_id: int
    score_state: str = "SCORED"
    score: WhoopRecoveryScore


# ── Sleep ───────────────────────────────────────────────────────────


class WhoopSleepStages(BaseModel):
    """Sleep stage breakdown from whoopskill sleep output."""

    total_in_bed_time_milli: int
    total_awake_time_milli: int
    total_light_sleep_time_milli: int
    total_slow_wave_sleep_time_milli: int
    total_rem_sleep_time_milli: int
    sleep_cycle_count: int
    disturbance_count: int


class WhoopSleepNeeded(BaseModel):
    """Sleep need calculation."""

    baseline_milli: int
    need_from_sleep_debt_milli: int = 0
    need_from_recent_strain_milli: int = 0


class WhoopSleepScore(BaseModel):
    """Sleep score payload."""

    stage_summary: WhoopSleepStages
    sleep_needed: Optional[WhoopSleepNeeded] = None
    respiratory_rate: Optional[float] = None
    sleep_performance_percentage: Optional[float] = None
    sleep_consistency_percentage: Optional[float] = None
    sleep_efficiency_percentage: Optional[float] = None


class WhoopSleep(BaseModel):
    """Single sleep record from whoopskill."""

    id: Optional[str] = None
    cycle_id: Optional[int] = None
    user_id: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    nap: bool = False
    score_state: str = "SCORED"
    score: WhoopSleepScore


# ── Cycle / Strain ──────────────────────────────────────────────────


class WhoopCycleScore(BaseModel):
    """Cycle score payload."""

    strain: float
    kilojoule: float
    average_heart_rate: int
    max_heart_rate: int


class WhoopCycle(BaseModel):
    """Single physiological cycle from whoopskill."""

    id: Optional[int] = None
    user_id: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    score_state: str = "SCORED"
    score: WhoopCycleScore


# ── Morning Briefing ────────────────────────────────────────────────


class MorningBriefing(BaseModel):
    """ADHD-tailored morning briefing generated from Whoop data.

    Maps recovery scores to executive function predictions and
    sleep metrics to ADHD-specific recommendations.
    """

    date: str  # YYYY-MM-DD
    recovery_score: int
    recovery_tier: RecoveryTier
    hrv_rmssd: float  # in milliseconds
    resting_hr: float
    sleep_performance: Optional[float] = None
    sws_percentage: float  # slow-wave sleep as % of total sleep
    rem_percentage: float  # REM as % of total sleep
    disturbance_count: int
    focus_recommendation: str
    recommended_focus_block_minutes: int
    sleep_notes: list[str]  # ADHD-specific sleep observations
    strain_yesterday: Optional[float] = None

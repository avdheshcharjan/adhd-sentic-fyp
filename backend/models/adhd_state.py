"""Pydantic models for ADHD behavioural metrics."""

from pydantic import BaseModel


class ADHDMetrics(BaseModel):
    """Snapshot of the rolling-window ADHD metrics engine."""

    context_switch_rate_5min: float = 0.0
    focus_score: float = 0.0
    distraction_ratio: float = 0.0
    current_streak_minutes: float = 0.0
    hyperfocus_detected: bool = False
    behavioral_state: str = "unknown"

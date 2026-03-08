"""
ADHD Metrics Engine — rolling-window behavioural analysis.

Uses in-memory collections.deque for O(1) append/pop operations:
  - activity_log: last 30 min at 2s intervals (maxlen=900)
  - app_switches: last 5 min switch timestamps (maxlen=150)

Computed metrics:
  - context_switch_rate_5min   — app switches in last 5 min
  - focus_score                — % time in productive sessions ≥ 15 min
  - distraction_ratio          — time in distracting vs total categorised time
  - current_streak_minutes     — consecutive minutes on current app
  - hyperfocus_detected        — 3+ hrs on a single non-priority task
  - behavioral_state           — focused | multitasking | distracted | hyperfocused | idle
"""

from collections import deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from models.adhd_state import ADHDMetrics


# Categories considered "productive"
PRODUCTIVE_CATEGORIES = {
    "development", "writing", "research", "productivity", "design",
}

# Categories considered "distracting"
DISTRACTING_CATEGORIES = {
    "social_media", "entertainment", "news", "shopping",
}


@dataclass
class ActivityEntry:
    """A single 2-second activity snapshot."""

    timestamp: datetime
    app_name: str
    category: str
    is_idle: bool


class ADHDMetricsEngine:
    """
    Rolling-window engine that computes real-time ADHD behavioural metrics
    from a stream of screen activity events.
    """

    def __init__(
        self,
        window_minutes: int = 30,
        poll_interval_seconds: int = 2,
    ) -> None:
        max_entries = (window_minutes * 60) // poll_interval_seconds  # 900
        self._activity_log: deque[ActivityEntry] = deque(maxlen=max_entries)
        self._switch_timestamps: deque[datetime] = deque(maxlen=150)

        self._last_app: str | None = None
        self._streak_start: datetime | None = None
        self._poll_interval = poll_interval_seconds

    # ── Public API ──────────────────────────────────────────────────

    def update(self, app_name: str, category: str, is_idle: bool, timestamp: datetime | None = None) -> ADHDMetrics:
        """
        Ingest a new activity event and return the updated metrics snapshot.
        This is the hot path — called every ~2 seconds.
        """
        ts = timestamp or datetime.now()
        entry = ActivityEntry(
            timestamp=ts,
            app_name=app_name,
            category=category,
            is_idle=is_idle,
        )
        self._activity_log.append(entry)

        # Track app switches
        if self._last_app is not None and app_name != self._last_app:
            self._switch_timestamps.append(ts)
            self._streak_start = ts
        elif self._last_app is None:
            self._streak_start = ts

        self._last_app = app_name

        return self.get_metrics()

    def get_metrics(self) -> ADHDMetrics:
        """Compute and return current ADHD metrics snapshot."""
        if not self._activity_log:
            return ADHDMetrics()

        now = self._activity_log[-1].timestamp

        switch_rate = self._compute_switch_rate(now)
        focus_score = self._compute_focus_score()
        distraction_ratio = self._compute_distraction_ratio()
        streak_minutes = self._compute_streak_minutes(now)
        hyperfocus = self._detect_hyperfocus(streak_minutes)
        state = self._derive_behavioral_state(
            switch_rate=switch_rate,
            focus_score=focus_score,
            distraction_ratio=distraction_ratio,
            streak_minutes=streak_minutes,
            hyperfocus=hyperfocus,
            is_idle=self._activity_log[-1].is_idle,
        )

        return ADHDMetrics(
            context_switch_rate_5min=switch_rate,
            focus_score=round(focus_score, 1),
            distraction_ratio=round(distraction_ratio, 2),
            current_streak_minutes=round(streak_minutes, 1),
            hyperfocus_detected=hyperfocus,
            behavioral_state=state,
        )

    # ── Private computation methods ─────────────────────────────────

    def _compute_switch_rate(self, now: datetime) -> float:
        """Count app switches in the last 5 minutes."""
        cutoff = now - timedelta(minutes=5)
        return sum(1 for ts in self._switch_timestamps if ts > cutoff)

    def _compute_focus_score(self) -> float:
        """
        Percentage of time spent in productive sessions lasting ≥ 15 min.
        Scans the activity log for consecutive productive stretches.
        """
        if not self._activity_log:
            return 0.0

        total_entries = len(self._activity_log)
        focused_entries = 0

        # Find consecutive productive streaks
        streak_count = 0
        threshold = (15 * 60) // self._poll_interval  # entries needed for 15 min

        for entry in self._activity_log:
            if entry.category in PRODUCTIVE_CATEGORIES and not entry.is_idle:
                streak_count += 1
            else:
                if streak_count >= threshold:
                    focused_entries += streak_count
                streak_count = 0

        # Don't forget the current streak
        if streak_count >= threshold:
            focused_entries += streak_count

        return (focused_entries / total_entries) * 100 if total_entries > 0 else 0.0

    def _compute_distraction_ratio(self) -> float:
        """
        Ratio of time in distracting apps vs total categorised time (0–1 scale).
        Entries with is_idle=True or category="system"/"other" are excluded.
        """
        distracting = 0
        categorised = 0

        for entry in self._activity_log:
            if entry.is_idle or entry.category in ("system", "other", "browser", "finance"):
                continue
            categorised += 1
            if entry.category in DISTRACTING_CATEGORIES:
                distracting += 1

        return distracting / categorised if categorised > 0 else 0.0

    def _compute_streak_minutes(self, now: datetime) -> float:
        """Minutes continuously on the current app."""
        if self._streak_start is None:
            return 0.0
        return (now - self._streak_start).total_seconds() / 60.0

    def _detect_hyperfocus(self, streak_minutes: float) -> bool:
        """Hyperfocus = 3+ hours on a single task."""
        return streak_minutes >= 180.0

    def _derive_behavioral_state(
        self,
        switch_rate: float,
        focus_score: float,
        distraction_ratio: float,
        streak_minutes: float,
        hyperfocus: bool,
        is_idle: bool,
    ) -> str:
        """
        Derive a single behavioural state label from computed metrics.

        Priority order: idle > hyperfocused > focused > distracted > multitasking > unknown
        """
        if is_idle:
            return "idle"
        if hyperfocus:
            return "hyperfocused"
        if switch_rate <= 4 and distraction_ratio < 0.3 and streak_minutes >= 5:
            return "focused"
        if switch_rate > 12 or distraction_ratio > 0.5:
            return "distracted"
        if switch_rate > 6:
            return "multitasking"
        return "focused"

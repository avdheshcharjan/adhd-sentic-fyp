"""
Transition-point detection engine.

Detects natural task breakpoints for intervention delivery. Based on
Iqbal & Bailey (CHI 2008): delivering notifications at coarse breakpoints
reduces frustration and resumption lag.

Rules:
  - Interventions are ONLY delivered at detected breakpoints
  - If no breakpoint within 5 min of trigger, downgrade to Tier 1 (ambient)
  - NEVER interrupt during sustained single-app focus (anti-pattern #4)
"""

from datetime import datetime, timedelta
from collections import deque
from enum import Enum


class BreakpointType(str, Enum):
    APP_SWITCH = "app_switch"
    TAB_BURST = "tab_burst"               # 3+ tab switches in 30 seconds
    IDLE_RESUME = "idle_resume"           # Returned from idle (>30s)
    FILE_SAVE = "file_save"              # Detected save operation in title
    DISTRACTION_ENTRY = "distraction_entry"
    SESSION_END = "session_end"


class TransitionDetector:
    """Detect natural task boundaries for non-disruptive intervention delivery."""

    # How long a detected breakpoint remains "fresh"
    BREAKPOINT_FRESHNESS_SECONDS: float = 10.0

    # Deep focus threshold — suppress ALL interventions after this
    DEEP_FOCUS_SUPPRESS_SECONDS: float = 900.0  # 15 minutes

    # Tab burst detection parameters
    TAB_BURST_COUNT: int = 3
    TAB_BURST_WINDOW_SECONDS: float = 30.0

    def __init__(self) -> None:
        self._recent_events: deque[dict] = deque(maxlen=100)
        self._current_app: str = ""
        self._current_app_since: datetime = datetime.now()
        self._last_breakpoint: datetime | None = None
        self._queued_intervention: dict | None = None

    # ── Event recording ──────────────────────────────────────────────

    def record_app_switch(
        self, from_app: str, to_app: str, timestamp: datetime | None = None,
    ) -> None:
        """Record an application switch event — always a coarse breakpoint."""
        ts = timestamp or datetime.now()
        self._recent_events.append({
            "type": "app_switch",
            "from": from_app,
            "to": to_app,
            "timestamp": ts,
        })
        self._current_app = to_app
        self._current_app_since = ts
        self._last_breakpoint = ts

    def record_tab_switch(
        self, url_or_title: str, timestamp: datetime | None = None,
    ) -> None:
        """Record a browser tab switch."""
        ts = timestamp or datetime.now()
        self._recent_events.append({
            "type": "tab_switch",
            "target": url_or_title,
            "timestamp": ts,
        })
        # Check for tab burst
        if self._detect_tab_burst(ts):
            self._last_breakpoint = ts

    def record_idle_start(self, timestamp: datetime | None = None) -> None:
        ts = timestamp or datetime.now()
        self._recent_events.append({"type": "idle_start", "timestamp": ts})

    def record_idle_end(self, timestamp: datetime | None = None) -> None:
        ts = timestamp or datetime.now()
        self._recent_events.append({"type": "idle_end", "timestamp": ts})
        self._last_breakpoint = ts

    # ── Query methods ────────────────────────────────────────────────

    def is_at_breakpoint(self, now: datetime | None = None) -> bool:
        """True if the user is currently at a natural task boundary.

        A breakpoint is "fresh" for BREAKPOINT_FRESHNESS_SECONDS after detection.
        """
        if self._last_breakpoint is None:
            return False
        current = now or datetime.now()
        elapsed = (current - self._last_breakpoint).total_seconds()
        return elapsed < self.BREAKPOINT_FRESHNESS_SECONDS

    def detect_breakpoint_type(self, now: datetime | None = None) -> BreakpointType | None:
        """Classify the most recent breakpoint type."""
        if not self._recent_events:
            return None

        current = now or datetime.now()
        last_event = self._recent_events[-1]

        if last_event["type"] == "app_switch":
            return BreakpointType.APP_SWITCH

        if self._detect_tab_burst(current):
            return BreakpointType.TAB_BURST

        if last_event["type"] == "idle_end":
            return BreakpointType.IDLE_RESUME

        return None

    def get_focus_duration_seconds(self, now: datetime | None = None) -> float:
        """How long the user has been on the current app without switching."""
        current = now or datetime.now()
        return (current - self._current_app_since).total_seconds()

    def should_suppress_intervention(self, now: datetime | None = None) -> bool:
        """True if user is in deep focus and should NOT be interrupted.

        Anti-pattern #4: NEVER interrupt productive hyperfocus.
        This is the HARD BLOCK — no intervention of any tier passes through.
        """
        return self.get_focus_duration_seconds(now) > self.DEEP_FOCUS_SUPPRESS_SECONDS

    # ── Private helpers ──────────────────────────────────────────────

    def _detect_tab_burst(self, now: datetime) -> bool:
        """3+ tab switches in 30 seconds = tab burst (user is scanning)."""
        cutoff = now - timedelta(seconds=self.TAB_BURST_WINDOW_SECONDS)
        recent_tabs = [
            e for e in self._recent_events
            if e["type"] == "tab_switch" and e["timestamp"] > cutoff
        ]
        return len(recent_tabs) >= self.TAB_BURST_COUNT

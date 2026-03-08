"""
Unit tests for the ADHD Metrics Engine.

Covers:
  - Context switch rate computation
  - Focus score calculation
  - Distraction ratio
  - Streak tracking
  - Hyperfocus detection
  - Behavioral state transitions
  - Deque memory limits
"""

from datetime import datetime, timedelta

from services.adhd_metrics import ADHDMetricsEngine


def _engine() -> ADHDMetricsEngine:
    return ADHDMetricsEngine()


# ── Context Switch Rate ─────────────────────────────────────────────


class TestContextSwitchRate:
    def test_no_switches(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        for i in range(10):
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update("VSCode", "development", False, ts)
        assert metrics.context_switch_rate_5min == 0

    def test_switches_counted(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        apps = ["VSCode", "Slack", "VSCode", "Chrome", "VSCode"]
        for i, app in enumerate(apps):
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update(app, "development", False, ts)
        # Switches: VSCode→Slack, Slack→VSCode, VSCode→Chrome, Chrome→VSCode = 4
        assert metrics.context_switch_rate_5min == 4

    def test_old_switches_excluded(self):
        """Switches older than 5 min should not be counted."""
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)

        # Create an old switch at t=0
        engine.update("VSCode", "development", False, base)
        engine.update("Slack", "communication", False, base + timedelta(seconds=2))

        # Now jump 6 minutes forward — the old switch is stale
        later = base + timedelta(minutes=6)
        metrics = engine.update("Slack", "communication", False, later)
        assert metrics.context_switch_rate_5min == 0


# ── Focus Score ─────────────────────────────────────────────────────


class TestFocusScore:
    def test_no_data_returns_zero(self):
        engine = _engine()
        metrics = engine.get_metrics()
        assert metrics.focus_score == 0.0

    def test_short_productive_streak_no_focus(self):
        """Less than 15 min of productive work should yield 0 focus score."""
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 2 min of productive work
        for i in range(60):  # 60 entries * 2s = 2 min
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update("VSCode", "development", False, ts)
        assert metrics.focus_score == 0.0

    def test_long_productive_streak_gives_focus(self):
        """16+ min productive session should give non-zero focus score."""
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 16 min = 480 entries at 2s
        for i in range(480):
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update("VSCode", "development", False, ts)
        assert metrics.focus_score > 0


# ── Distraction Ratio ───────────────────────────────────────────────


class TestDistractionRatio:
    def test_all_productive(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        for i in range(10):
            ts = base + timedelta(seconds=i * 2)
            engine.update("VSCode", "development", False, ts)
        metrics = engine.get_metrics()
        assert metrics.distraction_ratio == 0.0

    def test_all_distracting(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        for i in range(10):
            ts = base + timedelta(seconds=i * 2)
            engine.update("Reddit", "social_media", False, ts)
        metrics = engine.get_metrics()
        assert metrics.distraction_ratio == 1.0

    def test_mixed_ratio(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 5 productive + 5 distracting
        for i in range(5):
            ts = base + timedelta(seconds=i * 2)
            engine.update("VSCode", "development", False, ts)
        for i in range(5, 10):
            ts = base + timedelta(seconds=i * 2)
            engine.update("YouTube", "entertainment", False, ts)
        metrics = engine.get_metrics()
        assert 0.4 <= metrics.distraction_ratio <= 0.6


# ── Streak Tracking ────────────────────────────────────────────────


class TestStreakTracking:
    def test_streak_grows(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        for i in range(30):  # 30 * 2s = 1 min
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update("VSCode", "development", False, ts)
        assert metrics.current_streak_minutes >= 0.9

    def test_streak_resets_on_switch(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 1 min on VSCode
        for i in range(30):
            ts = base + timedelta(seconds=i * 2)
            engine.update("VSCode", "development", False, ts)
        # Switch to Slack
        ts = base + timedelta(seconds=61)
        metrics = engine.update("Slack", "communication", False, ts)
        assert metrics.current_streak_minutes < 0.1


# ── Hyperfocus Detection ───────────────────────────────────────────


class TestHyperfocusDetection:
    def test_no_hyperfocus_under_180_min(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 2 hours = 120 min, well under threshold
        for i in range(60):
            ts = base + timedelta(minutes=i * 2)
            engine.update("VSCode", "development", False, ts)
        metrics = engine.get_metrics()
        assert not metrics.hyperfocus_detected

    def test_hyperfocus_at_180_min(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # 181 min on one app
        for i in range(91):
            ts = base + timedelta(minutes=i * 2)
            engine.update("VSCode", "development", False, ts)
        metrics = engine.get_metrics()
        assert metrics.hyperfocus_detected


# ── Behavioral State Transitions ───────────────────────────────────


class TestBehavioralState:
    def test_idle_state(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        metrics = engine.update("VSCode", "development", True, base)
        assert metrics.behavioral_state == "idle"

    def test_focused_state(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # Stay on one productive app for 6 min → focused
        for i in range(180):  # 180 * 2s = 6 min
            ts = base + timedelta(seconds=i * 2)
            metrics = engine.update("VSCode", "development", False, ts)
        assert metrics.behavioral_state == "focused"

    def test_distracted_state(self):
        """Rapid switching between many apps → distracted."""
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        apps = ["VSCode", "Slack", "Chrome", "Spotify", "Reddit"]
        for i in range(50):
            ts = base + timedelta(seconds=i * 2)
            app = apps[i % len(apps)]
            category = "social_media" if app == "Reddit" else "entertainment" if app == "Spotify" else "development"
            metrics = engine.update(app, category, False, ts)
        # High switch rate + distracting content → distracted
        assert metrics.behavioral_state in ("distracted", "multitasking")


# ── Deque Memory Limits ────────────────────────────────────────────


class TestDequeMemory:
    def test_activity_log_maxlen(self):
        engine = _engine()
        base = datetime(2026, 3, 8, 12, 0, 0)
        # Insert 1000 entries, maxlen=900
        for i in range(1000):
            ts = base + timedelta(seconds=i * 2)
            engine.update("VSCode", "development", False, ts)
        assert len(engine._activity_log) == 900

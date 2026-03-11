"""
Unit tests for the Transition Detector.

Covers:
  - App switch creates a breakpoint
  - Breakpoint expires after freshness window
  - Tab burst detection (3+ in 30s)
  - Idle resume breakpoint
  - Deep focus (15+ min) suppresses interventions
"""

from datetime import datetime, timedelta

from services.transition_detector import TransitionDetector, BreakpointType


class TestAppSwitchBreakpoint:
    def test_app_switch_creates_breakpoint(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_app_switch("VSCode", "Slack", now)
        assert td.is_at_breakpoint(now)

    def test_breakpoint_type_is_app_switch(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_app_switch("VSCode", "Slack", now)
        assert td.detect_breakpoint_type(now) == BreakpointType.APP_SWITCH

    def test_breakpoint_expires_after_freshness(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_app_switch("VSCode", "Slack", now)
        # 11 seconds later — expired
        later = now + timedelta(seconds=11)
        assert not td.is_at_breakpoint(later)

    def test_breakpoint_still_fresh_within_window(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_app_switch("VSCode", "Slack", now)
        # 5 seconds later — still fresh
        later = now + timedelta(seconds=5)
        assert td.is_at_breakpoint(later)


class TestTabBurst:
    def test_no_burst_with_fewer_than_3_tabs(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_tab_switch("tab1", now)
        td.record_tab_switch("tab2", now + timedelta(seconds=5))
        assert not td.is_at_breakpoint(now + timedelta(seconds=6))

    def test_burst_with_3_tabs_in_30s(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_tab_switch("tab1", now)
        td.record_tab_switch("tab2", now + timedelta(seconds=10))
        td.record_tab_switch("tab3", now + timedelta(seconds=20))
        assert td.is_at_breakpoint(now + timedelta(seconds=20))

    def test_burst_type_detected(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_tab_switch("tab1", now)
        td.record_tab_switch("tab2", now + timedelta(seconds=10))
        td.record_tab_switch("tab3", now + timedelta(seconds=20))
        assert td.detect_breakpoint_type(now + timedelta(seconds=20)) == BreakpointType.TAB_BURST


class TestIdleResume:
    def test_idle_end_creates_breakpoint(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_idle_start(now)
        resume = now + timedelta(seconds=60)
        td.record_idle_end(resume)
        assert td.is_at_breakpoint(resume)

    def test_idle_resume_type(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td.record_idle_start(now)
        resume = now + timedelta(seconds=60)
        td.record_idle_end(resume)
        assert td.detect_breakpoint_type(resume) == BreakpointType.IDLE_RESUME


class TestDeepFocusSuppression:
    def test_no_suppression_under_15_min(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td._current_app_since = now - timedelta(minutes=10)
        assert not td.should_suppress_intervention(now)

    def test_suppression_after_15_min(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td._current_app_since = now - timedelta(minutes=16)
        assert td.should_suppress_intervention(now)

    def test_no_breakpoint_when_no_events(self):
        td = TransitionDetector()
        assert not td.is_at_breakpoint()

    def test_focus_duration_tracking(self):
        td = TransitionDetector()
        now = datetime(2026, 3, 9, 12, 0, 0)
        td._current_app_since = now - timedelta(minutes=30)
        duration = td.get_focus_duration_seconds(now)
        assert abs(duration - 1800) < 1  # 30 min = 1800s

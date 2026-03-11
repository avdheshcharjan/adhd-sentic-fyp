"""
Unit tests for the Hyperfocus Classifier.

Covers:
  - Sessions under 45 min return None
  - Productive categories → protect
  - Unproductive categories → gentle redirect
  - Ambiguous (browser) classification
  - Late night modifier (ambiguous → unproductive)
  - Priority app override
"""

from services.hyperfocus_classifier import HyperfocusClassifier, HyperfocusType


def _classifier() -> HyperfocusClassifier:
    return HyperfocusClassifier()


class TestSessionThreshold:
    def test_under_45min_returns_none(self):
        hf = _classifier()
        result = hf.classify(
            current_app="VSCode", app_category="development",
            session_duration_minutes=30, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] is None
        assert result["action"] == "none"

    def test_exactly_45min_triggers_classification(self):
        hf = _classifier()
        result = hf.classify(
            current_app="VSCode", app_category="development",
            session_duration_minutes=45, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] is not None


class TestProductive:
    def test_development_is_productive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="VSCode", app_category="development",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE
        assert result["action"] == "protect"
        assert result["suppress_interventions"] is True

    def test_writing_is_productive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Word", app_category="writing",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE

    def test_research_is_productive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Scholar", app_category="research",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE


class TestUnproductive:
    def test_social_media_is_unproductive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Reddit", app_category="social_media",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.UNPRODUCTIVE
        assert result["action"] == "gentle_redirect"
        assert result["suppress_interventions"] is False

    def test_entertainment_is_unproductive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="YouTube", app_category="entertainment",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.UNPRODUCTIVE


class TestAmbiguous:
    def test_browser_is_ambiguous(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Chrome", app_category="browser",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
        )
        assert result["type"] == HyperfocusType.AMBIGUOUS
        assert result["action"] == "check_in"


class TestLateNight:
    def test_late_night_makes_ambiguous_unproductive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Chrome", app_category="browser",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=23,
        )
        assert result["type"] == HyperfocusType.UNPRODUCTIVE

    def test_late_night_early_morning(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Chrome", app_category="browser",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=3,
        )
        assert result["type"] == HyperfocusType.UNPRODUCTIVE

    def test_late_night_does_not_affect_productive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="VSCode", app_category="development",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=23,
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE


class TestPriorityOverride:
    def test_priority_app_always_productive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="Figma", app_category="other",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
            user_priority_apps=["Figma", "Sketch"],
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE

    def test_priority_case_insensitive(self):
        hf = _classifier()
        result = hf.classify(
            current_app="figma", app_category="other",
            session_duration_minutes=60, recent_switch_count=0, time_of_day=14,
            user_priority_apps=["Figma"],
        )
        assert result["type"] == HyperfocusType.PRODUCTIVE

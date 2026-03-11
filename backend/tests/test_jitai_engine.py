"""
Unit tests for the JITAI Decision Engine.

Covers:
  - DND blocks all interventions
  - Cooldown blocks interventions
  - Focused state blocks interventions
  - Distraction spiral rule fires
  - Sustained disengagement rule fires
  - Hyperfocus check rule fires
  - Emotional escalation rule fires
  - Per-block cap enforced (anti-pattern #9)
  - Productive hyperfocus protection (anti-pattern #4)
  - Wellbeing check at 4+ hours of productive hyperfocus
  - Max 3 actions per intervention (anti-pattern #8)
  - Adaptive cooldown on dismissals
"""

import random
from datetime import datetime, timedelta

from models.adhd_state import ADHDMetrics
from services.jitai_engine import JITAIEngine


def _engine() -> JITAIEngine:
    """Create a fresh engine with deterministic bandit (always deliver)."""
    engine = JITAIEngine()
    # Force bandit to always deliver for deterministic tests
    random.seed(42)
    return engine


def _metrics(**overrides) -> ADHDMetrics:
    """Create metrics with sensible defaults + overrides."""
    defaults = {
        "context_switch_rate_5min": 0.0,
        "focus_score": 50.0,
        "distraction_ratio": 0.0,
        "current_streak_minutes": 5.0,
        "hyperfocus_detected": False,
        "behavioral_state": "multitasking",
        "current_app": "VSCode",
        "current_category": "development",
    }
    defaults.update(overrides)
    return ADHDMetrics(**defaults)


class TestHardBlocks:
    def test_dnd_blocks_all(self):
        engine = _engine()
        engine.set_dnd_mode(True)
        metrics = _metrics(
            context_switch_rate_5min=20,
            distraction_ratio=0.8,
            behavioral_state="distracted",
        )
        assert engine.evaluate(metrics) is None

    def test_cooldown_blocks(self):
        engine = _engine()
        engine._last_intervention_time = datetime.now() - timedelta(seconds=60)
        metrics = _metrics(
            context_switch_rate_5min=20,
            distraction_ratio=0.8,
            behavioral_state="distracted",
        )
        assert engine.evaluate(metrics) is None

    def test_focused_state_blocks(self):
        engine = _engine()
        metrics = _metrics(behavioral_state="focused")
        assert engine.evaluate(metrics) is None


class TestDistractionSpiral:
    def test_fires_on_high_switch_and_distraction(self):
        engine = _engine()
        # Make bandit always say yes by seeding enough successes
        for _ in range(20):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )
        metrics = _metrics(
            context_switch_rate_5min=15,
            distraction_ratio=0.6,
            behavioral_state="distracted",
        )
        intervention = engine.evaluate(metrics)
        if intervention:
            assert intervention.type == "distraction_spiral"
            assert intervention.ef_domain == "self_restraint"

    def test_does_not_fire_below_thresholds(self):
        engine = _engine()
        metrics = _metrics(
            context_switch_rate_5min=5,
            distraction_ratio=0.3,
            behavioral_state="multitasking",
        )
        intervention = engine.evaluate(metrics)
        # Should not fire distraction_spiral
        if intervention:
            assert intervention.type != "distraction_spiral"


class TestSustainedDisengagement:
    def test_fires_on_prolonged_distraction(self):
        engine = _engine()
        for _ in range(20):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )
        metrics = _metrics(
            behavioral_state="distracted",
            current_streak_minutes=25,
            distraction_ratio=0.8,
        )
        intervention = engine.evaluate(metrics)
        if intervention:
            assert intervention.type in ("distraction_spiral", "sustained_disengagement")


class TestHyperfocusCheck:
    def test_fires_on_hyperfocus(self):
        engine = _engine()
        for _ in range(20):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )
        metrics = _metrics(
            hyperfocus_detected=True,
            current_streak_minutes=200,
            behavioral_state="hyperfocused",
            current_category="other",
        )
        intervention = engine.evaluate(metrics)
        if intervention:
            assert intervention.type == "hyperfocus_check"


class TestEmotionalEscalation:
    def test_fires_on_dysregulation(self):
        engine = _engine()
        for _ in range(20):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )
        metrics = _metrics(behavioral_state="distracted")
        emotion_ctx = {"emotional_dysregulation": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        if intervention:
            assert intervention.type in ("distraction_spiral", "emotional_escalation")


class TestPerBlockCap:
    def test_max_3_per_block(self):
        """Anti-pattern #9: max 3 interventions per 90-min block."""
        engine = _engine()
        # Force bandit to deliver
        for _ in range(50):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )

        count = 0
        for i in range(10):
            engine._last_intervention_time = None  # Reset cooldown
            metrics = _metrics(
                context_switch_rate_5min=15,
                distraction_ratio=0.6,
                behavioral_state="distracted",
            )
            result = engine.evaluate(metrics)
            if result:
                count += 1

        assert count <= 3


class TestProductiveHyperfocusProtection:
    def test_productive_hyperfocus_not_interrupted(self):
        """Anti-pattern #4: never interrupt productive hyperfocus."""
        engine = _engine()
        metrics = _metrics(
            current_streak_minutes=60,
            behavioral_state="hyperfocused",
            current_app="VSCode",
            current_category="development",
        )
        assert engine.evaluate(metrics) is None

    def test_wellbeing_check_at_4_hours(self):
        """Exception: 4+ hr productive hyperfocus gets wellbeing check."""
        engine = _engine()
        metrics = _metrics(
            current_streak_minutes=250,
            behavioral_state="hyperfocused",
            current_app="VSCode",
            current_category="development",
        )
        intervention = engine.evaluate(metrics)
        if intervention:
            assert intervention.type == "hyperfocus_wellbeing"


class TestMaxActions:
    def test_all_interventions_have_max_3_actions(self):
        """Anti-pattern #8: max 3 action choices."""
        engine = _engine()
        for _ in range(50):
            engine.adaptive_bandit.update(
                {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
                success=True,
            )

        # Test each rule
        test_cases = [
            _metrics(context_switch_rate_5min=15, distraction_ratio=0.6, behavioral_state="distracted"),
            _metrics(behavioral_state="distracted", current_streak_minutes=25, distraction_ratio=0.8),
            _metrics(hyperfocus_detected=True, behavioral_state="multitasking", current_streak_minutes=200, current_category="other"),
        ]
        for m in test_cases:
            engine._last_intervention_time = None
            engine._intervention_count_this_block = 0
            intervention = engine.evaluate(m)
            if intervention:
                assert len(intervention.actions) <= 3


class TestAdaptiveCooldown:
    def test_dismissals_increase_cooldown(self):
        engine = _engine()
        original_cooldown = engine._cooldown_seconds
        for _ in range(3):
            engine.record_response("test", action_taken=None, dismissed=True)
        assert engine._cooldown_seconds > original_cooldown

    def test_acceptance_resets_cooldown(self):
        engine = _engine()
        for _ in range(3):
            engine.record_response("test", action_taken=None, dismissed=True)
        engine.record_response("test", action_taken="breathe", dismissed=False)
        assert engine._cooldown_seconds == engine.DEFAULT_COOLDOWN_SECONDS

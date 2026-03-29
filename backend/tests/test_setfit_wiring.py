"""
Manual verification tests for SetFit wiring fixes.

Tests:
  1. Emotion Radar: SetFit label → PASE scores in dashboard endpoint
  2. JITAI: Emotion-aware rules fire when SetFit detects negative states
  3. Confidence: SetFit confidence is stored and used for blending
"""

from datetime import datetime

from models.adhd_state import ADHDMetrics
from services.jitai_engine import JITAIEngine
from services.setfit_service import (
    SETFIT_TO_ADHD_STATE,
    SETFIT_TO_PASE,
    blend_pase,
    setfit_classifier,
)


# ── Helpers ───────────────────────────────────────────────────────────────

def _engine() -> JITAIEngine:
    """Fresh engine with bandit primed to always deliver."""
    engine = JITAIEngine()
    for _ in range(30):
        engine.adaptive_bandit.update(
            {"hour": datetime.now().hour, "whoop_recovery": 50, "minutes_since_last": 999},
            success=True,
        )
    return engine


def _metrics(**overrides) -> ADHDMetrics:
    defaults = {
        "context_switch_rate_5min": 0.0,
        "focus_score": 50.0,
        "distraction_ratio": 0.0,
        "current_streak_minutes": 5.0,
        "hyperfocus_detected": False,
        "behavioral_state": "multitasking",
        "current_app": "Chrome",
        "current_category": "browser",
    }
    defaults.update(overrides)
    return ADHDMetrics(**defaults)


# ── 1. Emotion Radar: blend_pase produces correct PASE profiles ──────────

class TestEmotionRadarPASE:
    def test_all_labels_have_pase_mapping(self):
        for label in ["joyful", "focused", "frustrated", "anxious", "disengaged", "overwhelmed"]:
            assert label in SETFIT_TO_PASE
            pase = SETFIT_TO_PASE[label]
            assert set(pase.keys()) == {"pleasantness", "attention", "sensitivity", "aptitude"}

    def test_blend_pase_high_confidence_near_canonical(self):
        canonical = SETFIT_TO_PASE["frustrated"]
        blended = blend_pase("frustrated", 0.95)
        for key in canonical:
            assert abs(blended[key] - canonical[key]) < 0.05

    def test_blend_pase_low_confidence_near_neutral(self):
        blended = blend_pase("frustrated", 0.1)
        for key, value in blended.items():
            assert abs(value - 0.5) < 0.1  # Should be very close to neutral

    def test_blend_pase_zero_confidence_is_neutral(self):
        blended = blend_pase("overwhelmed", 0.0)
        for value in blended.values():
            assert value == 0.5

    def test_all_pase_values_in_range(self):
        for label in SETFIT_TO_PASE:
            for conf in [0.0, 0.3, 0.5, 0.7, 1.0]:
                blended = blend_pase(label, conf)
                for key, value in blended.items():
                    assert 0.0 <= value <= 1.0, f"{label} conf={conf} {key}={value}"

    def test_unknown_label_falls_back_to_disengaged(self):
        blended = blend_pase("nonexistent_label", 0.8)
        expected = blend_pase("disengaged", 0.8)
        assert blended == expected


# ── 2. SetFit classifier produces valid labels + confidence ──────────────

class TestSetFitClassifier:
    def test_predict_returns_valid_label(self):
        label, confidence = setfit_classifier.predict("I can't focus on anything today")
        assert label in SETFIT_TO_PASE
        assert label in SETFIT_TO_ADHD_STATE

    def test_predict_returns_confidence_in_range(self):
        _, confidence = setfit_classifier.predict("Everything is going great!")
        assert 0.0 <= confidence <= 1.0

    def test_predict_frustrated_text(self):
        label, confidence = setfit_classifier.predict("This stupid bug won't go away no matter what I try")
        assert label in SETFIT_TO_PASE
        assert confidence > 0.0

    def test_predict_joyful_text(self):
        label, confidence = setfit_classifier.predict("I finally got it working, this is amazing!")
        assert label in SETFIT_TO_PASE


# ── 3. JITAI: Existing Rule 4a (overwhelmed → emotional_escalation) ─────

class TestJITAIRule4aEmotionalEscalation:
    def test_fires_with_emotion_context(self):
        engine = _engine()
        metrics = _metrics(behavioral_state="distracted")
        emotion_ctx = {"emotional_dysregulation": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is not None
        assert intervention.type == "emotional_escalation"
        assert intervention.ef_domain == "self_regulation_emotion"
        assert len(intervention.actions) <= 3

    def test_does_not_fire_without_emotion_context(self):
        engine = _engine()
        metrics = _metrics(behavioral_state="distracted")
        intervention = engine.evaluate(metrics)
        # Without emotion context, Rule 4a should not fire
        assert intervention is None or intervention.type != "emotional_escalation"


# ── 4. JITAI: New Rule 4b (frustration + context switching) ──────────────

class TestJITAIRule4bFrustration:
    def test_fires_on_frustration_and_switching(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            context_switch_rate_5min=10,
            distraction_ratio=0.3,
        )
        emotion_ctx = {"frustration_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is not None
        assert intervention.type == "frustration_spiral"
        assert intervention.ef_domain == "self_regulation_emotion"

    def test_does_not_fire_with_low_switches(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            context_switch_rate_5min=3,
        )
        emotion_ctx = {"frustration_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is None or intervention.type != "frustration_spiral"


# ── 5. JITAI: New Rule 4c (anxiety + distraction) ───────────────────────

class TestJITAIRule4cAnxiety:
    def test_fires_on_anxiety_and_distraction(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            distraction_ratio=0.5,
        )
        emotion_ctx = {"anxiety_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is not None
        assert intervention.type == "anxiety_distraction"
        assert intervention.ef_domain == "self_regulation_emotion"

    def test_does_not_fire_with_low_distraction(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            distraction_ratio=0.2,
        )
        emotion_ctx = {"anxiety_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is None or intervention.type != "anxiety_distraction"


# ── 6. JITAI: New Rule 4d (disengaged persistence) ──────────────────────

class TestJITAIRule4dDisengaged:
    def test_fires_on_sustained_disengagement(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            current_streak_minutes=15,
        )
        emotion_ctx = {"disengaged_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is not None
        assert intervention.type == "emotion_disengagement"
        assert intervention.ef_domain == "self_motivation"

    def test_does_not_fire_under_10_minutes(self):
        engine = _engine()
        metrics = _metrics(
            behavioral_state="distracted",
            current_streak_minutes=5,
        )
        emotion_ctx = {"disengaged_detected": True}
        intervention = engine.evaluate(metrics, emotion_ctx)
        assert intervention is None or intervention.type != "emotion_disengagement"


# ── 7. All new interventions respect max 3 actions (anti-pattern #8) ─────

class TestNewRulesMaxActions:
    def test_all_new_rules_have_max_3_actions(self):
        engine = _engine()

        test_cases = [
            (
                _metrics(behavioral_state="distracted", context_switch_rate_5min=10),
                {"frustration_detected": True},
            ),
            (
                _metrics(behavioral_state="distracted", distraction_ratio=0.5),
                {"anxiety_detected": True},
            ),
            (
                _metrics(behavioral_state="distracted", current_streak_minutes=15),
                {"disengaged_detected": True},
            ),
            (
                _metrics(behavioral_state="distracted"),
                {"emotional_dysregulation": True},
            ),
        ]

        for metrics, emotion_ctx in test_cases:
            engine._last_intervention_time = None
            engine._intervention_count_this_block = 0
            intervention = engine.evaluate(metrics, emotion_ctx)
            if intervention:
                assert len(intervention.actions) <= 3, f"{intervention.type} has {len(intervention.actions)} actions"


# ── 8. Confidence gating: low confidence should NOT trigger emotion rules ─

class TestConfidenceGating:
    def test_screen_activity_emotion_context_gates_on_confidence(self):
        """Simulate what screen.py builds — low confidence should not set flags."""
        # Simulating the screen.py emotion_context building logic
        setfit_label = "overwhelmed"
        setfit_confidence = 0.4  # Below 0.7 threshold

        emotion_context = {
            "setfit_label": setfit_label,
            "setfit_confidence": setfit_confidence,
            "primary_adhd_state": SETFIT_TO_ADHD_STATE[setfit_label],
            "emotional_dysregulation": setfit_label == "overwhelmed" and setfit_confidence > 0.7,
            "frustration_detected": setfit_label == "frustrated" and setfit_confidence > 0.7,
            "anxiety_detected": setfit_label == "anxious" and setfit_confidence > 0.7,
            "disengaged_detected": setfit_label == "disengaged" and setfit_confidence > 0.6,
        }

        # All emotion flags should be False due to low confidence
        assert emotion_context["emotional_dysregulation"] is False
        assert emotion_context["frustration_detected"] is False
        assert emotion_context["anxiety_detected"] is False
        assert emotion_context["disengaged_detected"] is False

        # JITAI should not fire emotion rules
        engine = _engine()
        metrics = _metrics(behavioral_state="distracted")
        intervention = engine.evaluate(metrics, emotion_context)
        assert intervention is None or intervention.type not in (
            "emotional_escalation", "frustration_spiral", "anxiety_distraction", "emotion_disengagement",
        )

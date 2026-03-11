"""
Unit tests for the XAI Concept Bottleneck Explainer.

Covers:
  - Progressive disclosure tiers (3-tier structure)
  - Emoji mapping per intervention type
  - One-sentence generation
  - WHAT / WHY / HOW explanation triplet
  - User correction payload generation
  - Urgency colour (warm spectrum, never blue)
"""

from services.xai_explainer import ConceptBottleneckExplainer


def _explainer() -> ConceptBottleneckExplainer:
    return ConceptBottleneckExplainer()


class TestProgressiveDisclosure:
    def test_returns_three_tiers(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            intervention_type="distraction_spiral",
            metrics={"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert hasattr(result, "tier_1")
        assert hasattr(result, "tier_2")
        assert hasattr(result, "tier_3")

    def test_tier1_has_color_and_emoji(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            intervention_type="distraction_spiral",
            metrics={"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert result.tier_1.color in ("green", "amber", "orange", "red")
        assert result.tier_1.emoji != ""

    def test_tier2_has_sentence(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            intervention_type="distraction_spiral",
            metrics={"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert isinstance(result.tier_2.sentence, str)
        assert len(result.tier_2.sentence) > 0

    def test_tier3_has_concepts_list(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            intervention_type="distraction_spiral",
            metrics={"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert isinstance(result.tier_3.concepts, list)


class TestEmojiMapping:
    def test_distraction_spiral_emoji(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "distraction_spiral", {"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert result.tier_1.emoji == "🌀"

    def test_emotional_escalation_emoji(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "emotional_escalation", {},
        )
        assert result.tier_1.emoji == "🌊"

    def test_hyperfocus_check_emoji(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "hyperfocus_check", {"current_streak_minutes": 200},
        )
        assert result.tier_1.emoji == "⏰"

    def test_hyperfocus_wellbeing_emoji(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "hyperfocus_wellbeing", {"current_streak_minutes": 300},
        )
        assert result.tier_1.emoji == "💧"


class TestExplanationTriplet:
    def test_what_contains_metrics(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "distraction_spiral",
            {"context_switch_rate_5min": 15, "distraction_ratio": 0.6},
        )
        assert "15" in result.what
        assert "60" in result.what  # 0.6 * 100 = 60%

    def test_why_with_senticnet(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "emotional_escalation",
            {},
            senticnet_result={
                "emotion_profile": {"primary_emotion": "anger"},
                "adhd_signals": {"intensity_score": -75},
            },
        )
        assert "anger" in result.why

    def test_why_without_senticnet(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "distraction_spiral", {},
        )
        assert "ADHD" in result.why or "executive function" in result.why

    def test_how_is_counterfactual(self):
        explainer = _explainer()
        result = explainer.explain_intervention(
            "distraction_spiral", {},
        )
        assert len(result.how) > 0


class TestUserCorrection:
    def test_correction_payload(self):
        explainer = _explainer()
        correction = explainer.apply_user_correction(
            concept_id="frustration_level",
            user_value=0.1,
            system_prediction=0.8,
        )
        assert correction.concept_id == "frustration_level"
        assert correction.user_correction == 0.1
        assert correction.system_prediction == 0.8

    def test_correction_without_system_prediction(self):
        explainer = _explainer()
        correction = explainer.apply_user_correction(
            concept_id="emotional_valence",
            user_value=0.9,
        )
        assert correction.system_prediction is None


class TestWarmSpectrum:
    def test_no_blue_urgency_colors(self):
        """Anti-pattern #10: never use blue."""
        explainer = _explainer()
        for itype in [
            "distraction_spiral", "sustained_disengagement",
            "hyperfocus_check", "emotional_escalation", "hyperfocus_wellbeing",
        ]:
            result = explainer.explain_intervention(itype, {})
            assert "blue" not in result.tier_1.color.lower()

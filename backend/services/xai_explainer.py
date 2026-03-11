"""
XAI Explanation Engine — Concept Bottleneck + counterfactual explanations.

Architecture:
  Raw data → Feature extraction → SenticNet concept activations →
  Behavioural prediction → Explanation

Three explanation types:
  WHAT: "Your switching pattern shows signs of attention fragmentation"
  WHY:  "SenticNet detected frustration (0.82) in your recent activity"
  HOW:  "If you take a 5-min break, your focus typically improves by ~40%"

Progressive disclosure (anti-pattern #3 — NEVER auto-expand):
  Tier 1: Traffic light + emoji (always shown)
  Tier 2: One-sentence concept explanation (tap to expand)
  Tier 3: Full detail + user correction option (tap again)
"""

from datetime import datetime

from models.explanation import (
    ExplanationTier1,
    ExplanationTier2,
    ExplanationTier3,
    ExplanationTier3Detail,
    InterventionExplanation,
    ConceptCorrection,
)


class ConceptBottleneckExplainer:
    """Generates human-readable explanations using SenticNet concept outputs."""

    # Concept definitions that users can correct
    CONCEPT_DEFINITIONS: dict[str, dict] = {
        "emotional_valence": {
            "source": "senticnet_polarity",
            "label": "Mood",
            "description": "Whether your recent writing/activity feels positive or negative",
            "user_correctable": True,
        },
        "frustration_level": {
            "source": "senticnet_temper + keyboard_error_rate",
            "label": "Frustration",
            "description": "Signs of frustration in your activity patterns",
            "user_correctable": True,
        },
        "attention_consistency": {
            "source": "mouse_entropy + switch_rate + typing_variance",
            "label": "Focus stability",
            "description": "How steady your attention has been",
            "user_correctable": True,
        },
        "physiological_readiness": {
            "source": "whoop_recovery + hr_trend",
            "label": "Energy level",
            "description": "Your body's readiness based on Whoop data",
            "user_correctable": False,  # Physiological data is objective
        },
        "engagement_level": {
            "source": "senticnet_engagement",
            "label": "Engagement",
            "description": "How engaged you appear to be with your current task",
            "user_correctable": True,
        },
    }

    # ── Public API ──────────────────────────────────────────────────

    def explain_intervention(
        self,
        intervention_type: str,
        metrics: dict,
        senticnet_result: dict | None = None,
    ) -> InterventionExplanation:
        """Generate an explainable justification for a JITAI intervention."""

        what = self._explain_what(intervention_type, metrics)
        why = self._explain_why(intervention_type, metrics, senticnet_result)
        how = self._explain_how(intervention_type)

        # Build concept activations from metrics + senticnet
        concept_activations = self._extract_concept_activations(
            metrics, senticnet_result,
        )

        # Progressive disclosure tiers
        tier_1 = ExplanationTier1(
            color=self._urgency_color(intervention_type),
            emoji=self._get_emoji(intervention_type),
        )
        tier_2 = ExplanationTier2(
            sentence=self._build_summary_sentence(
                intervention_type, concept_activations,
            ),
        )
        tier_3 = self._build_tier3(concept_activations)

        return InterventionExplanation(
            what=what,
            why=why,
            how=how,
            tier_1=tier_1,
            tier_2=tier_2,
            tier_3=tier_3,
        )

    def apply_user_correction(
        self,
        concept_id: str,
        user_value: float,
        system_prediction: float | None = None,
    ) -> ConceptCorrection:
        """Process a user correction of a concept prediction.

        Feeds back into the Concept Bottleneck Model for retraining.
        """
        return ConceptCorrection(
            concept_id=concept_id,
            system_prediction=system_prediction,
            user_correction=user_value,
            timestamp=datetime.now(),
        )

    # ── WHAT / WHY / HOW templates ──────────────────────────────────

    def _explain_what(self, intervention_type: str, metrics: dict) -> str:
        """Observation-level explanation."""
        templates = {
            "distraction_spiral": (
                f"You've switched apps {metrics.get('context_switch_rate_5min', 0):.0f} "
                f"times in the last 5 minutes, with "
                f"{metrics.get('distraction_ratio', 0) * 100:.0f}% of time on non-work apps."
            ),
            "sustained_disengagement": (
                f"You've been away from focused work for "
                f"{metrics.get('current_streak_minutes', 0):.0f} minutes."
            ),
            "hyperfocus_check": (
                f"You've been on the same task for "
                f"{metrics.get('current_streak_minutes', 0) / 60:.1f} hours."
            ),
            "emotional_escalation": (
                "Your recent activity patterns suggest emotional intensity is rising."
            ),
            "hyperfocus_wellbeing": (
                f"You've been deeply focused for "
                f"{metrics.get('current_streak_minutes', 0) / 60:.1f} hours."
            ),
        }
        return templates.get(
            intervention_type, "A pattern was detected in your activity.",
        )

    def _explain_why(
        self,
        intervention_type: str,
        metrics: dict,
        senticnet: dict | None,
    ) -> str:
        """Concept-level reasoning."""
        if senticnet and senticnet.get("emotion_profile"):
            emotion = senticnet["emotion_profile"].get("primary_emotion", "")
            intensity = senticnet.get("adhd_signals", {}).get(
                "intensity_score", 0,
            )
            return (
                f"Emotional analysis detected {emotion} "
                f"(intensity: {abs(intensity):.0f}/100). "
                f"This maps to executive function challenges with "
                f"focus and task initiation."
            )
        return (
            "This pattern is common in ADHD and relates to "
            "executive function differences."
        )

    def _explain_how(self, intervention_type: str) -> str:
        """Counterfactual — what would improve things."""
        counterfactuals = {
            "distraction_spiral": (
                "Research shows a 2-minute breathing reset can "
                "reduce context switching by ~40%."
            ),
            "sustained_disengagement": (
                "Starting with a 5-minute micro-task often "
                "breaks the avoidance cycle."
            ),
            "hyperfocus_check": (
                "Time-boxing the remaining work can preserve "
                "your focus while protecting other priorities."
            ),
            "emotional_escalation": (
                "Acknowledging the emotion (even briefly) helps "
                "regulate the prefrontal cortex response."
            ),
            "hyperfocus_wellbeing": (
                "Brief movement and hydration breaks preserve "
                "cognitive performance during extended focus."
            ),
        }
        return counterfactuals.get(intervention_type, "")

    # ── Progressive disclosure helpers ──────────────────────────────

    def _extract_concept_activations(
        self, metrics: dict, senticnet: dict | None,
    ) -> dict[str, float]:
        """Extract concept activation values from available data."""
        activations: dict[str, float] = {}

        # From metrics
        switch_rate = metrics.get("context_switch_rate_5min", 0)
        activations["attention_consistency"] = max(
            -1.0, 1.0 - (switch_rate / 12.0),
        )

        distraction = metrics.get("distraction_ratio", 0)
        activations["engagement_level"] = 1.0 - (distraction * 2)

        # From SenticNet (if available)
        if senticnet:
            ep = senticnet.get("emotion_profile", {})
            polarity_score = ep.get("polarity_score", 0)
            activations["emotional_valence"] = polarity_score / 100.0

            signals = senticnet.get("adhd_signals", {})
            intensity = signals.get("intensity_score", 0)
            activations["frustration_level"] = max(0, -intensity / 100.0)

        return activations

    def _build_summary_sentence(
        self, intervention_type: str, activations: dict[str, float],
    ) -> str:
        """One-sentence concept summary for Tier 2."""
        active_labels = [
            self.CONCEPT_DEFINITIONS[k]["label"]
            for k, v in activations.items()
            if abs(v) > 0.5 and k in self.CONCEPT_DEFINITIONS
        ]
        concept_str = " and ".join(active_labels[:2]) or "your activity"

        templates = {
            "distraction_spiral": (
                f"Your {concept_str} suggest your attention is jumping around."
            ),
            "sustained_disengagement": (
                f"Your {concept_str} show you've been away from "
                f"focused work for a while."
            ),
            "emotional_escalation": (
                f"Your {concept_str} indicate things are feeling intense."
            ),
            "hyperfocus_check": (
                f"Your {concept_str} show extended single-task focus."
            ),
            "hyperfocus_wellbeing": (
                f"Your {concept_str} show a very long focus session."
            ),
        }
        return templates.get(
            intervention_type,
            f"Noticing some changes in your {concept_str}.",
        )

    def _build_tier3(
        self, activations: dict[str, float],
    ) -> ExplanationTier3:
        """Build Tier 3 detailed breakdown with correction options."""
        details = []
        for concept_id, value in activations.items():
            if concept_id not in self.CONCEPT_DEFINITIONS:
                continue
            defn = self.CONCEPT_DEFINITIONS[concept_id]
            details.append(
                ExplanationTier3Detail(
                    concept=defn["label"],
                    value=value,
                    description=defn["description"],
                    can_correct=defn["user_correctable"],
                    correction_prompt=(
                        f"Am I wrong about your {defn['label'].lower()}?"
                        if defn["user_correctable"]
                        else None
                    ),
                ),
            )
        return ExplanationTier3(concepts=details)

    # ── Emoji / colour helpers ──────────────────────────────────────

    def _get_emoji(self, intervention_type: str) -> str:
        return {
            "distraction_spiral": "🌀",
            "sustained_disengagement": "💤",
            "hyperfocus_check": "⏰",
            "emotional_escalation": "🌊",
            "hyperfocus_wellbeing": "💧",
        }.get(intervention_type, "💡")

    def _urgency_color(self, intervention_type: str) -> str:
        """Warm spectrum only — anti-pattern #10."""
        return {
            "distraction_spiral": "amber",
            "sustained_disengagement": "amber",
            "hyperfocus_check": "green",
            "emotional_escalation": "orange",
            "hyperfocus_wellbeing": "green",
        }.get(intervention_type, "amber")

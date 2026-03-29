"""
4-tier SenticNet pipeline orchestrator.

Tier 1 (Safety):   depression + toxicity + intensity — runs FIRST, always
Tier 2 (Emotion):  emotion + polarity + subjectivity + sarcasm
Tier 3 (ADHD):     engagement + wellbeing + concepts + aspects
Tier 4 (Deep):     personality + ensemble — on demand only

Pipeline modes:
  - "full":         All 4 tiers (~2-3s) — for chat/venting
  - "lightweight":  emotion + engagement + intensity (3 APIs, <500ms)
  - "safety_only":  depression + toxicity + intensity (3 APIs, <500ms)
"""

import asyncio
import logging

from models.senticnet_result import (
    EmotionProfile,
    SafetyFlags,
    ADHDRelevantSignals,
    PersonalityProfile,
    SenticNetResult,
)
from services.senticnet_client import SenticNetClient
from services.setfit_service import setfit_classifier, SETFIT_TO_ADHD_STATE

logger = logging.getLogger("adhd-brain")


class SenticNetPipeline:
    """Safety-first affective computing pipeline."""

    def __init__(self):
        self.client = SenticNetClient()

    async def close(self):
        await self.client.close()

    # ── Public API ───────────────────────────────────────────────────

    async def analyze(self, text: str, mode: str = "full") -> SenticNetResult:
        """Run the SenticNet pipeline on input text.

        Args:
            text: Input text to analyze
            mode: "full", "lightweight", or "safety_only"

        Returns:
            SenticNetResult with populated fields based on mode
        """
        if mode == "safety_only":
            return await self._run_safety_only(text)
        elif mode == "lightweight":
            return await self._run_lightweight(text)
        else:
            return await self._run_full(text)

    # ── Full Pipeline (All 4 Tiers) ──────────────────────────────────

    async def _run_full(self, text: str) -> SenticNetResult:
        """Run all 4 tiers sequentially. ~2-3s total."""

        result = SenticNetResult(text=text, mode="full")

        # TIER 1: Safety — ALWAYS first
        safety = await self._tier1_safety(text)
        result.safety = safety

        if safety.is_critical:
            logger.warning(f"CRITICAL safety flag for: {text[:50]}...")
            # Emergency exit — skip remaining tiers
            return result

        # TIER 2: Emotion
        emotion = await self._tier2_emotion(text)
        result.emotion = emotion

        # Fix 2.2: Use secondary emotion when it's stronger than primary
        if emotion.emotion_details:
            parsed = SenticNetClient.parse_emotion_string(emotion.emotion_details)
            primary_score = parsed.get("primary_score", 0.0)
            secondary_emotion = parsed.get("secondary", "")
            secondary_score = parsed.get("secondary_score", 0.0)
            if secondary_score > primary_score and secondary_emotion:
                result.emotion.primary_emotion = secondary_emotion

        # TIER 3: ADHD Signals
        adhd = await self._tier3_adhd(text, intensity=safety.intensity_score)
        result.adhd_signals = adhd

        # TIER 4: Deep Analysis
        personality, ensemble_dict = await self._tier4_deep(text)
        result.personality = personality
        result.ensemble_raw = str(ensemble_dict) if ensemble_dict else None

        # Extract Hourglass dimensions from ensemble response
        if ensemble_dict:
            result.emotion.introspection = self._parse_float(ensemble_dict.get("introspection"))
            result.emotion.temper = self._parse_float(ensemble_dict.get("temper"))
            result.emotion.attitude = self._parse_float(ensemble_dict.get("attitude"))
            result.emotion.sensitivity = self._parse_float(ensemble_dict.get("sensitivity"))
            result.emotion.polarity_score = self._parse_float(ensemble_dict.get("intensity"))

            # Fix 2.7: Extract depression/toxicity/engagement/wellbeing from ensemble
            # These supplement Tier 1/3 signals and are used for veto gates below
            ensemble_depression = self._parse_percentage(ensemble_dict.get("depression"))
            ensemble_toxicity = self._parse_percentage(ensemble_dict.get("toxicity"))
            ensemble_engagement = self._parse_percentage(ensemble_dict.get("engagement"))
            ensemble_wellbeing = self._parse_percentage(ensemble_dict.get("wellbeing"))

            # Use ensemble values to supplement safety/adhd scores if available
            if ensemble_depression and result.safety.depression_score == 0.0:
                result.safety.depression_score = ensemble_depression
            if ensemble_toxicity and result.safety.toxicity_score == 0.0:
                result.safety.toxicity_score = ensemble_toxicity
            if ensemble_engagement and result.adhd_signals.engagement_score == 0.0:
                result.adhd_signals.engagement_score = ensemble_engagement
            if ensemble_wellbeing and result.adhd_signals.wellbeing_score == 0.0:
                result.adhd_signals.wellbeing_score = ensemble_wellbeing

        # SetFit override: replace SenticNet emotion label with 86%-accurate classifier
        setfit_label, setfit_confidence = setfit_classifier.predict(text)
        result.emotion.primary_emotion = setfit_label
        result.primary_adhd_state = SETFIT_TO_ADHD_STATE[setfit_label]
        result.setfit_confidence = setfit_confidence

        return result

    @staticmethod
    def _parse_percentage(value: str | None) -> float:
        """Parse a percentage string like '33.33%' → 33.33."""
        if value is None:
            return 0.0
        try:
            return float(str(value).strip().rstrip("%"))
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _parse_float(value: str | float | None) -> float:
        """Safely parse a float from ensemble string values."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    # ── Lightweight Pipeline (3 APIs) ────────────────────────────────

    async def _run_lightweight(self, text: str) -> SenticNetResult:
        """Quick analysis: emotion + engagement + intensity. <500ms target."""

        result = SenticNetResult(text=text, mode="lightweight")

        # Run 3 APIs concurrently
        emotion_raw, engagement_raw, intensity_raw = await asyncio.gather(
            self.client.get_emotion(text),
            self.client.get_engagement(text),
            self.client.get_intensity(text),
            return_exceptions=True,
        )

        # Parse emotion
        if isinstance(emotion_raw, str):
            parsed = SenticNetClient.parse_emotion_string(emotion_raw)
            result.emotion = EmotionProfile(
                primary_emotion=parsed.get("primary", "unknown"),
                emotion_details=emotion_raw,
            )

        # Parse engagement
        engagement = 0.0
        if isinstance(engagement_raw, (int, float)):
            engagement = float(engagement_raw)

        # Parse intensity
        intensity = 0.0
        if isinstance(intensity_raw, (int, float)):
            intensity = float(intensity_raw)

        result.adhd_signals = ADHDRelevantSignals(
            engagement_score=engagement,
            intensity_score=intensity,
            **ADHDRelevantSignals.derive_flags(engagement, 0.0, intensity),
        )

        # SetFit override: replace SenticNet emotion label with 86%-accurate classifier
        setfit_label, setfit_confidence = setfit_classifier.predict(text)
        result.emotion.primary_emotion = setfit_label
        result.primary_adhd_state = SETFIT_TO_ADHD_STATE[setfit_label]
        result.setfit_confidence = setfit_confidence

        return result

    # ── Safety-Only Pipeline (3 APIs) ────────────────────────────────

    async def _run_safety_only(self, text: str) -> SenticNetResult:
        """Safety check: depression + toxicity + intensity. <500ms target."""

        result = SenticNetResult(text=text, mode="safety_only")
        result.safety = await self._tier1_safety(text)
        return result

    # ── Tier Implementations ─────────────────────────────────────────

    async def _tier1_safety(self, text: str) -> SafetyFlags:
        """Tier 1: Depression + Toxicity + Intensity (concurrent)."""

        depression_raw, toxicity_raw, intensity_raw = await asyncio.gather(
            self.client.get_depression(text),
            self.client.get_toxicity(text),
            self.client.get_intensity(text),
            return_exceptions=True,
        )

        depression = float(depression_raw) if isinstance(depression_raw, (int, float)) else 0.0
        toxicity = float(toxicity_raw) if isinstance(toxicity_raw, (int, float)) else 0.0
        intensity = float(intensity_raw) if isinstance(intensity_raw, (int, float)) else 0.0

        level = SafetyFlags.compute_level(depression, toxicity, intensity)

        return SafetyFlags(
            level=level,
            depression_score=depression,
            toxicity_score=toxicity,
            intensity_score=intensity,
            is_critical=(level == "critical"),
        )

    async def _tier2_emotion(self, text: str) -> EmotionProfile:
        """Tier 2: Emotion + Polarity + Subjectivity + Sarcasm (concurrent)."""

        emotion_raw, polarity_raw, subjectivity_raw, sarcasm_raw = await asyncio.gather(
            self.client.get_emotion(text),
            self.client.get_polarity(text),
            self.client.get_subjectivity(text),
            self.client.get_sarcasm(text),
            return_exceptions=True,
        )

        # Parse emotion
        primary_emotion = "unknown"
        emotion_details = ""
        if isinstance(emotion_raw, str):
            parsed = SenticNetClient.parse_emotion_string(emotion_raw)
            primary_emotion = parsed.get("primary", "unknown")
            emotion_details = emotion_raw

        # Parse polarity
        polarity = "neutral"
        if isinstance(polarity_raw, str):
            polarity = polarity_raw.lower()

        # Parse subjectivity
        is_subjective = True
        if isinstance(subjectivity_raw, str):
            is_subjective = "objective" not in subjectivity_raw.lower()

        # Parse sarcasm
        sarcasm_detected = False
        sarcasm_details = ""
        if isinstance(sarcasm_raw, str):
            sarcasm_details = sarcasm_raw
            sarcasm_detected = "no sarcasm" not in sarcasm_raw.lower()

        return EmotionProfile(
            primary_emotion=primary_emotion,
            emotion_details=emotion_details,
            polarity=polarity,
            is_subjective=is_subjective,
            sarcasm_detected=sarcasm_detected,
            sarcasm_details=sarcasm_details,
        )

    async def _tier3_adhd(
        self, text: str, intensity: float = 0.0
    ) -> ADHDRelevantSignals:
        """Tier 3: Engagement + Wellbeing + Concepts + Aspects (concurrent)."""

        engagement_raw, wellbeing_raw, concepts_raw, aspects_raw = await asyncio.gather(
            self.client.get_engagement(text),
            self.client.get_wellbeing(text),
            self.client.get_concepts(text),
            self.client.get_aspects(text),
            return_exceptions=True,
        )

        engagement = float(engagement_raw) if isinstance(engagement_raw, (int, float)) else 0.0
        wellbeing = float(wellbeing_raw) if isinstance(wellbeing_raw, (int, float)) else 0.0

        # Parse concepts (Fix 3.5: strip Python repr artifacts)
        concepts: list[str] = []
        if isinstance(concepts_raw, str) and concepts_raw:
            cleaned = concepts_raw.strip("[]'\"")
            concepts = [c.strip().strip("'\"") for c in cleaned.split(",") if c.strip()]

        # Parse aspects
        aspects = ""
        if isinstance(aspects_raw, str):
            aspects = aspects_raw

        flags = ADHDRelevantSignals.derive_flags(engagement, wellbeing, intensity)

        return ADHDRelevantSignals(
            engagement_score=engagement,
            wellbeing_score=wellbeing,
            intensity_score=intensity,
            concepts=concepts,
            aspects=aspects,
            **flags,
        )

    async def _tier4_deep(self, text: str) -> tuple[PersonalityProfile | None, dict | None]:
        """Tier 4: Personality + Ensemble (concurrent, on demand).

        Returns the ensemble as a parsed dict (not stringified) so _run_full()
        can extract Hourglass dimensions.
        """

        personality_raw, ensemble_raw = await asyncio.gather(
            self.client.get_personality(text),
            self.client.get_ensemble(text),
            return_exceptions=True,
        )

        # Parse personality
        personality = None
        if isinstance(personality_raw, str):
            parsed = SenticNetClient.parse_personality_string(personality_raw)
            personality = PersonalityProfile(
                raw=personality_raw,
                mbti_type=parsed.get("mbti", ""),
                openness=parsed.get("O", ""),
                conscientiousness=parsed.get("C", ""),
                extraversion=parsed.get("E", ""),
                agreeableness=parsed.get("A", ""),
                neuroticism=parsed.get("N", ""),
            )

        # Return ensemble as dict for Hourglass extraction
        ensemble_dict: dict | None = None
        if isinstance(ensemble_raw, dict):
            ensemble_dict = ensemble_raw

        return personality, ensemble_dict

    # ── Phase 4: Hourglass → ADHD State Mapping ─────────────────────

    def map_hourglass_to_adhd_state(self, hourglass: dict) -> dict:
        """Map SenticNet Hourglass of Emotions to ADHD-relevant states.

        Hourglass dimensions (each -1 to +1):
          Introspection: Joy (+) ↔ Sadness (-)
          Temper: Calmness (+) ↔ Anger (-)
          Attitude: Pleasantness (+) ↔ Disgust (-)
          Sensitivity: Eagerness (+) ↔ Fear (-)

        ADHD state interpretations:
          Low Introspection + Low Sensitivity = boredom-driven disengagement
          Low Temper + Low Introspection = frustration spiral (core trigger)
          High Attitude negativity = shame/RSD
          High Sensitivity + High Introspection = productive flow (don't interrupt!)
          Rapid oscillation across Temper/Introspection = emotional dysregulation
        """
        introspection = hourglass.get("introspection", 0)
        temper = hourglass.get("temper", 0)
        attitude = hourglass.get("attitude", 0)
        sensitivity = hourglass.get("sensitivity", 0)

        adhd_states = {
            "boredom_disengagement": introspection < -0.3 and sensitivity < -0.2,
            "frustration_spiral": temper < -0.4 and introspection < -0.2,
            "shame_rsd": attitude < -0.5,
            "productive_flow": sensitivity > 0.3 and introspection > 0.3,
            "emotional_dysregulation": abs(temper) > 0.6 or abs(introspection) > 0.7,
            "anxiety_comorbid": sensitivity < -0.5 and temper < 0,
        }

        primary = "neutral"
        for state, is_active in adhd_states.items():
            if is_active:
                primary = state
                break

        return {
            "primary_adhd_state": primary,
            "all_states": {k: v for k, v in adhd_states.items() if v},
            "hourglass_raw": hourglass,
            "recommended_ef_domain": self._map_state_to_ef_domain(primary),
        }

    @staticmethod
    def _map_state_to_ef_domain(state: str) -> str:
        """Map ADHD emotional state to Barkley's EF deficit domain."""
        mapping = {
            "boredom_disengagement": "self_motivation",
            "frustration_spiral": "self_regulation_emotion",
            "shame_rsd": "self_regulation_emotion",
            "productive_flow": "none",
            "emotional_dysregulation": "self_regulation_emotion",
            "anxiety_comorbid": "self_regulation_emotion",
            "neutral": "none",
        }
        return mapping.get(state, "none")

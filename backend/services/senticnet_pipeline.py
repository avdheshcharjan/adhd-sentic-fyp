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
            logger.warning(f"🔴 CRITICAL safety flag for: {text[:50]}...")
            # Emergency exit — skip remaining tiers
            return result

        # TIER 2: Emotion
        emotion = await self._tier2_emotion(text)
        result.emotion = emotion

        # TIER 3: ADHD Signals
        adhd = await self._tier3_adhd(text, intensity=safety.intensity_score)
        result.adhd_signals = adhd

        # TIER 4: Deep Analysis
        personality, ensemble_raw = await self._tier4_deep(text)
        result.personality = personality
        result.ensemble_raw = ensemble_raw

        return result

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

        # Parse concepts
        concepts = []
        if isinstance(concepts_raw, str) and concepts_raw:
            concepts = [c.strip() for c in concepts_raw.split(",") if c.strip()]

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

    async def _tier4_deep(self, text: str) -> tuple[PersonalityProfile | None, str | None]:
        """Tier 4: Personality + Ensemble (concurrent, on demand)."""

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

        # Ensemble raw for debugging
        ensemble_str = None
        if isinstance(ensemble_raw, dict):
            ensemble_str = str(ensemble_raw)
        elif isinstance(ensemble_raw, str):
            ensemble_str = ensemble_raw

        return personality, ensemble_str

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

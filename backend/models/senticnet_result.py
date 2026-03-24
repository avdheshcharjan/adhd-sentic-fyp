"""Pydantic models for SenticNet pipeline results."""

from pydantic import BaseModel, Field


class EmotionProfile(BaseModel):
    """Core emotional analysis from SenticNet Tier 2."""

    primary_emotion: str = "unknown"
    emotion_details: str = ""  # Raw emotion string, e.g. "fear (99.7%) & annoyance (50.0%)"

    # Hourglass of Emotions — 4 affective dimensions (-100 to 100)
    introspection: float = 0.0  # pleasantness: joy ↔ sadness
    temper: float = 0.0         # attention: interest ↔ disgust  (called "temper" in API)
    attitude: float = 0.0       # aptitude: trust ↔ surprise    (called "attitude" in API)
    sensitivity: float = 0.0    # sensitivity: fear ↔ anger

    polarity: str = "neutral"   # "positive", "negative", "neutral"
    polarity_score: float = 0.0  # from intensity API (-100 to 100)

    is_subjective: bool = True
    sarcasm_detected: bool = False
    sarcasm_details: str = ""


class SafetyFlags(BaseModel):
    """Safety-critical flags from SenticNet Tier 1.

    Safety is non-negotiable — this runs FIRST in every pipeline.
    """

    level: str = "normal"  # "critical", "high", "moderate", "normal"
    depression_score: float = 0.0  # 0-100 (from percentage)
    toxicity_score: float = 0.0    # 0-100
    intensity_score: float = 0.0   # -100 to 100

    is_critical: bool = False  # True if emergency response needed

    @staticmethod
    def compute_level(depression: float, toxicity: float, intensity: float) -> str:
        """Determine safety level from scores.

        CRITICAL: depression > 70 AND toxicity > 60
        HIGH: depression > 70 OR intensity < -80
        MODERATE: toxicity > 50
        NORMAL: below all thresholds
        """
        if depression > 70 and toxicity > 60:
            return "critical"
        if depression > 70 or intensity < -80:
            return "high"
        if toxicity > 50:
            return "moderate"
        return "normal"


class ADHDRelevantSignals(BaseModel):
    """ADHD-specific derived signals from SenticNet Tier 3."""

    engagement_score: float = 0.0   # -100 to 100
    wellbeing_score: float = 0.0    # -100 to 100
    intensity_score: float = 0.0    # -100 to 100 (shared with SafetyFlags)

    # Derived boolean flags
    is_disengaged: bool = False       # engagement < -30
    is_overwhelmed: bool = False      # intensity > 70 AND wellbeing < -20
    is_frustrated: bool = False       # intensity < -50 AND engagement < 0
    emotional_dysregulation: bool = False  # abs(intensity) > 80

    # Concept and aspect extraction
    concepts: list[str] = Field(default_factory=list)
    aspects: str = ""

    @staticmethod
    def derive_flags(
        engagement: float, wellbeing: float, intensity: float
    ) -> dict[str, bool]:
        """Compute ADHD-relevant boolean flags from raw scores."""
        return {
            "is_disengaged": engagement < -30,
            "is_overwhelmed": intensity > 70 and wellbeing < -20,
            "is_frustrated": intensity < -50 and engagement < 0,
            "emotional_dysregulation": abs(intensity) > 80,
        }


class PersonalityProfile(BaseModel):
    """Big 5 personality traits from SenticNet Tier 4."""

    raw: str = ""  # e.g. "ENTJ (O↑C↑E↑A↓N↓)"
    mbti_type: str = ""
    openness: str = ""        # ↑ or ↓
    conscientiousness: str = ""
    extraversion: str = ""
    agreeableness: str = ""
    neuroticism: str = ""


class SenticNetResult(BaseModel):
    """Combined output of a full SenticNet pipeline run."""

    text: str  # Original input text
    mode: str  # "full", "lightweight", "safety_only"
    safety: SafetyFlags = Field(default_factory=SafetyFlags)
    emotion: EmotionProfile = Field(default_factory=EmotionProfile)
    adhd_signals: ADHDRelevantSignals = Field(default_factory=ADHDRelevantSignals)
    personality: PersonalityProfile | None = None
    ensemble_raw: str | None = None  # Raw ensemble response for debugging
    primary_adhd_state: str = "neutral"  # Mapped from Hourglass dimensions

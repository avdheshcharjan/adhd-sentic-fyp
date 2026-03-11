"""
Five-tier calm notification architecture.

Replaces the single InterventionPopup with a 5-level escalation system.

Tier 1: Ambient color shift on menu bar icon (user may not notice)
Tier 2: Gentle pulse animation on menu bar icon
Tier 3: Non-activating overlay panel (doesn't steal focus)
Tier 4: Toast notification with optional sound
Tier 5: Full notification (reserved for safety + hard deadlines only)

Core principle: use the MINIMUM tier that will be effective.
Anti-pattern #10: warm spectrum colours only (green→amber→orange→red, never blue).
"""

from enum import IntEnum


class NotificationTier(IntEnum):
    """Five escalation levels. Lower tiers require less attention."""

    AMBIENT_COLOR = 1
    GENTLE_PULSE = 2
    OVERLAY_PANEL = 3
    TOAST_NOTIFICATION = 4
    FULL_NOTIFICATION = 5


def select_tier(
    intervention_type: str,
    behavioral_state: str,
    minutes_since_last_intervention: float,
    whoop_recovery_tier: str = "yellow",
    adhd_severity: str = "low_positive",
) -> int:
    """Select the appropriate notification tier based on context.

    Args:
        intervention_type: Type of intervention (e.g. "distraction_spiral")
        behavioral_state: Current behavioural state from metrics engine
        minutes_since_last_intervention: Minutes since last intervention shown
        whoop_recovery_tier: "green", "yellow", or "red"
        adhd_severity: ASRS severity band

    Returns:
        Notification tier (1–5).
    """
    # Safety escalation — always Tier 5
    if intervention_type == "safety_critical":
        return NotificationTier.FULL_NOTIFICATION

    # Hyperfocus wellbeing check (4+ hours) — Tier 3 maximum
    if intervention_type == "hyperfocus_wellbeing":
        return NotificationTier.OVERLAY_PANEL

    # Low Whoop recovery day — be gentler, use Tier 1
    if whoop_recovery_tier == "red":
        return NotificationTier.AMBIENT_COLOR

    # First intervention of the session — start gentle
    if minutes_since_last_intervention > 60:
        return NotificationTier.AMBIENT_COLOR

    # If user is actively distracted (scrolling social media), Tier 3
    if behavioral_state == "distracted":
        return NotificationTier.OVERLAY_PANEL

    # Repeated disengagement within 30 min — escalate to Tier 3
    if (
        intervention_type == "sustained_disengagement"
        and minutes_since_last_intervention < 30
    ):
        return NotificationTier.OVERLAY_PANEL

    # Default: ambient awareness
    return NotificationTier.GENTLE_PULSE


def urgency_color_for_tier(tier: int) -> str:
    """Map notification tier to warm-spectrum colour.

    Anti-pattern #10: NEVER use blue as primary UI colour for ADHD indicators.
    """
    return {
        NotificationTier.AMBIENT_COLOR: "green",
        NotificationTier.GENTLE_PULSE: "amber",
        NotificationTier.OVERLAY_PANEL: "amber",
        NotificationTier.TOAST_NOTIFICATION: "orange",
        NotificationTier.FULL_NOTIFICATION: "red",
    }.get(tier, "amber")

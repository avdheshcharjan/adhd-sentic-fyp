"""
Unit tests for the Notification Tier selector.

Covers:
  - Safety critical → Tier 5
  - Low Whoop recovery → Tier 1
  - Distracted state → Tier 3
  - First intervention of session → Tier 1
  - Hyperfocus wellbeing → Tier 3
  - Sustained disengagement recent → Tier 3
  - Default → Tier 2
  - Urgency colour mapping (warm spectrum)
"""

from services.notification_tier import (
    select_tier,
    urgency_color_for_tier,
    NotificationTier,
)


class TestTierSelection:
    def test_safety_critical_always_tier_5(self):
        tier = select_tier(
            intervention_type="safety_critical",
            behavioral_state="distracted",
            minutes_since_last_intervention=5,
        )
        assert tier == NotificationTier.FULL_NOTIFICATION

    def test_hyperfocus_wellbeing_capped_at_tier_3(self):
        tier = select_tier(
            intervention_type="hyperfocus_wellbeing",
            behavioral_state="hyperfocused",
            minutes_since_last_intervention=300,
        )
        assert tier == NotificationTier.OVERLAY_PANEL

    def test_low_whoop_recovery_tier_1(self):
        tier = select_tier(
            intervention_type="distraction_spiral",
            behavioral_state="distracted",
            minutes_since_last_intervention=10,
            whoop_recovery_tier="red",
        )
        assert tier == NotificationTier.AMBIENT_COLOR

    def test_first_intervention_of_session_tier_1(self):
        tier = select_tier(
            intervention_type="distraction_spiral",
            behavioral_state="distracted",
            minutes_since_last_intervention=120,
        )
        assert tier == NotificationTier.AMBIENT_COLOR

    def test_distracted_state_tier_3(self):
        tier = select_tier(
            intervention_type="distraction_spiral",
            behavioral_state="distracted",
            minutes_since_last_intervention=10,
        )
        assert tier == NotificationTier.OVERLAY_PANEL

    def test_sustained_disengagement_recent_tier_3(self):
        tier = select_tier(
            intervention_type="sustained_disengagement",
            behavioral_state="multitasking",
            minutes_since_last_intervention=15,
        )
        assert tier == NotificationTier.OVERLAY_PANEL

    def test_default_tier_2(self):
        tier = select_tier(
            intervention_type="distraction_spiral",
            behavioral_state="multitasking",
            minutes_since_last_intervention=45,
        )
        assert tier == NotificationTier.GENTLE_PULSE


class TestUrgencyColor:
    def test_tier_1_green(self):
        assert urgency_color_for_tier(1) == "green"

    def test_tier_2_amber(self):
        assert urgency_color_for_tier(2) == "amber"

    def test_tier_3_amber(self):
        assert urgency_color_for_tier(3) == "amber"

    def test_tier_4_orange(self):
        assert urgency_color_for_tier(4) == "orange"

    def test_tier_5_red(self):
        assert urgency_color_for_tier(5) == "red"

    def test_no_blue_anywhere(self):
        """Anti-pattern #10: never use blue."""
        for tier_val in range(1, 6):
            color = urgency_color_for_tier(tier_val)
            assert "blue" not in color.lower()

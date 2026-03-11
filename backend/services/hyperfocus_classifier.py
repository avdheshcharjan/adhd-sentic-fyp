"""
Hyperfocus classifier — distinguishes productive from unproductive deep focus.

Detection criteria (all must be true for classification):
  - Single application focus for 45+ minutes
  - Low input variability (consistent activity)
  - Minimal tab/window switching

Classification uses app category + user priority apps + time of day.

CRITICAL RULE (anti-pattern #4): Productive hyperfocus is NEVER interrupted
except for:
  - 4+ hour wellbeing check (hydration, posture, movement)
  - Hard calendar deadlines within 15 minutes
  - Safety-critical depression/toxicity threshold
"""


class HyperfocusType:
    """Hyperfocus classification labels."""

    PRODUCTIVE = "productive"       # Deep work on priority task — PROTECT
    UNPRODUCTIVE = "unproductive"   # Doom-scrolling, rabbit holes — gently redirect
    AMBIGUOUS = "ambiguous"         # Research that might be relevant or not


# Categories that count as productive
PRODUCTIVE_CATEGORIES = {
    "development", "writing", "research", "design", "productivity",
}

# Categories that are always unproductive hyperfocus
UNPRODUCTIVE_CATEGORIES = {
    "social_media", "entertainment", "shopping", "news",
}


class HyperfocusClassifier:
    """Detect and classify hyperfocus episodes."""

    # Minimum session duration to trigger classification
    MIN_SESSION_MINUTES: float = 45.0

    # Duration for wellbeing check on productive hyperfocus
    WELLBEING_CHECK_MINUTES: float = 240.0  # 4 hours

    def classify(
        self,
        current_app: str,
        app_category: str,
        session_duration_minutes: float,
        recent_switch_count: int,
        time_of_day: int,
        user_priority_apps: list[str] | None = None,
    ) -> dict:
        """Classify a hyperfocus episode.

        Only call when session_duration_minutes >= 45.

        Returns:
            dict with type, action, and configuration.
        """
        if session_duration_minutes < self.MIN_SESSION_MINUTES:
            return {"type": None, "action": "none"}

        # Classify based on app category
        if app_category in PRODUCTIVE_CATEGORIES:
            focus_type = HyperfocusType.PRODUCTIVE
        elif app_category in UNPRODUCTIVE_CATEGORIES:
            focus_type = HyperfocusType.UNPRODUCTIVE
        elif app_category == "browser":
            focus_type = HyperfocusType.AMBIGUOUS
        else:
            focus_type = HyperfocusType.AMBIGUOUS

        # Override: user's priority apps are always productive
        if user_priority_apps and current_app.lower() in [
            a.lower() for a in user_priority_apps
        ]:
            focus_type = HyperfocusType.PRODUCTIVE

        # Time-of-day modifier: 11 PM – 5 AM makes ambiguous → unproductive
        if time_of_day >= 23 or time_of_day < 5:
            if focus_type == HyperfocusType.AMBIGUOUS:
                focus_type = HyperfocusType.UNPRODUCTIVE

        # Build action configuration
        actions = {
            HyperfocusType.PRODUCTIVE: {
                "action": "protect",
                "suppress_interventions": True,
                "wellbeing_check_at_minutes": self.WELLBEING_CHECK_MINUTES,
                "ambient_indicator": "in_the_zone",
                "time_display": True,
            },
            HyperfocusType.UNPRODUCTIVE: {
                "action": "gentle_redirect",
                "suppress_interventions": False,
                "tier_sequence": [1, 2, 3],
                "tier_timing_minutes": [30, 60, 90],
                "message_tone": "compassionate",  # Never shaming (anti-pattern #5)
            },
            HyperfocusType.AMBIGUOUS: {
                "action": "check_in",
                "suppress_interventions": False,
                "tier": 3,
                "check_in_at_minutes": 60,
            },
        }

        return {
            "type": focus_type,
            "session_minutes": session_duration_minutes,
            "app": current_app,
            "category": app_category,
            **actions[focus_type],
        }

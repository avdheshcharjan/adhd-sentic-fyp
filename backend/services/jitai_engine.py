"""
JITAI Decision Engine — Just-in-Time Adaptive Intervention.

Implements Barkley's 5 Executive Function deficit domains with
4 gating layers from the supplement:

  Gate 0: Transition detector — delivery only at breakpoints
  Gate 1: Hyperfocus protection — never interrupt productive deep work
  Gate 2: Per-block cap — max 3 per 90 min (anti-pattern #9)
  Gate 3: Adaptive bandit — Thompson Sampling decides IF to deliver

4 intervention rules:
  1. Distraction spiral       → self_restraint
  2. Sustained disengagement  → self_motivation
  3. Hyperfocus check         → self_management_time
  4. Emotional escalation     → self_regulation_emotion

Anti-patterns enforced:
  #4: Never interrupt productive hyperfocus
  #5: Always upward framing
  #8: Max 3 action choices
  #9: Max 3 interventions per 90-min block
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from models.adhd_state import ADHDMetrics
from models.intervention import Intervention, InterventionAction
from services.transition_detector import TransitionDetector
from services.hyperfocus_classifier import HyperfocusClassifier
from services.adaptive_frequency import ThompsonSamplingBandit
from services.notification_tier import select_tier, urgency_color_for_tier

if TYPE_CHECKING:
    from services.brain_dump_reminder import BrainDumpReminderQueue


class JITAIEngine:
    """Core intervention decision engine."""

    # Default configuration
    DEFAULT_COOLDOWN_SECONDS: int = 300   # 5 min
    MAX_COOLDOWN_SECONDS: int = 1800      # 30 min
    DEFAULT_MAX_PER_BLOCK: int = 3
    BLOCK_DURATION_MINUTES: float = 90.0

    def __init__(self, brain_dump_reminders: BrainDumpReminderQueue | None = None) -> None:
        self.transition_detector = TransitionDetector()
        self.hyperfocus_classifier = HyperfocusClassifier()
        self.adaptive_bandit = ThompsonSamplingBandit()
        self._brain_dump_reminders = brain_dump_reminders

        self._last_intervention_time: datetime | None = None
        self._cooldown_seconds: int = self.DEFAULT_COOLDOWN_SECONDS
        self._dismissed_count: int = 0
        self._dnd_mode: bool = False

        # Per-block cap tracking
        self._intervention_count_this_block: int = 0
        self._block_start_time: datetime = datetime.now()

        # Configurable caps (can be overridden by ADHDProfile)
        self._max_per_block: int = self.DEFAULT_MAX_PER_BLOCK

    # ── Public API ──────────────────────────────────────────────────

    def evaluate(
        self,
        metrics: ADHDMetrics,
        emotion_context: dict | None = None,
    ) -> Intervention | None:
        """Evaluate whether an intervention should be delivered.

        Args:
            metrics: Current ADHD behavioural metrics snapshot.
            emotion_context: Optional SenticNet signal flags.

        Returns:
            Intervention if one should be delivered, None otherwise.
        """
        now = datetime.now()

        # ── Hard blocks ──────────────────────────────────────────────
        if self._dnd_mode:
            return None

        if self._is_in_cooldown(now):
            return None

        if metrics.behavioral_state == "focused":
            return None

        # ── Gate 1: Hyperfocus protection (anti-pattern #4) ──────────
        if metrics.current_streak_minutes > 45:
            hf = self.hyperfocus_classifier.classify(
                current_app=metrics.current_app,
                app_category=metrics.current_category,
                session_duration_minutes=metrics.current_streak_minutes,
                recent_switch_count=int(metrics.context_switch_rate_5min),
                time_of_day=now.hour,
            )
            if hf["type"] == "productive" and hf.get("suppress_interventions"):
                # Only exception: 4+ hr wellbeing check
                if metrics.current_streak_minutes >= 240:
                    return self._wellbeing_check_intervention(metrics, now)
                return None

        # ── Gate 2: Per-block cap (anti-pattern #9) ──────────────────
        minutes_in_block = (now - self._block_start_time).total_seconds() / 60
        if minutes_in_block >= self.BLOCK_DURATION_MINUTES:
            # Reset block
            self._intervention_count_this_block = 0
            self._block_start_time = now
        elif self._intervention_count_this_block >= self._max_per_block:
            return None

        # ── Gate 3: Adaptive bandit ──────────────────────────────────
        bandit_context = {
            "hour": now.hour,
            "whoop_recovery": metrics.whoop_recovery_score or 50,
            "minutes_since_last": self._minutes_since_last(now),
        }
        if not self.adaptive_bandit.should_deliver(bandit_context):
            return None

        # ── Intervention rules ───────────────────────────────────────
        intervention = self._evaluate_rules(metrics, emotion_context)
        if intervention is None:
            return None

        # Assign notification tier + urgency colour
        intervention.notification_tier = select_tier(
            intervention_type=intervention.type,
            behavioral_state=metrics.behavioral_state,
            minutes_since_last_intervention=self._minutes_since_last(now),
            whoop_recovery_tier=metrics.whoop_recovery_tier or "yellow",
        )
        intervention.urgency_color = urgency_color_for_tier(
            intervention.notification_tier,
        )

        self._intervention_count_this_block += 1
        self._last_intervention_time = now

        return intervention

    def record_response(
        self,
        intervention_id: str,
        action_taken: str | None,
        dismissed: bool,
    ) -> None:
        """Track intervention effectiveness for adaptive calibration."""
        self._last_intervention_time = datetime.now()

        if dismissed:
            self._dismissed_count += 1
            if self._dismissed_count >= 3:
                self._cooldown_seconds = min(
                    int(self._cooldown_seconds * 1.5),
                    self.MAX_COOLDOWN_SECONDS,
                )
        else:
            self._dismissed_count = 0
            self._cooldown_seconds = self.DEFAULT_COOLDOWN_SECONDS

        # Update bandit with outcome
        success = not dismissed and action_taken is not None
        bandit_context = {
            "hour": datetime.now().hour,
            "whoop_recovery": 50,
            "minutes_since_last": 0,
        }
        self.adaptive_bandit.update(bandit_context, success)

    def set_dnd_mode(self, enabled: bool) -> None:
        """Toggle Do Not Disturb mode."""
        self._dnd_mode = enabled

    def set_max_per_block(self, max_count: int) -> None:
        """Override the per-block cap (from ADHDProfile)."""
        self._max_per_block = max_count

    # ── Intervention rules (Barkley's 5 EF domains) ─────────────────

    def _evaluate_rules(
        self,
        metrics: ADHDMetrics,
        emotion_context: dict | None,
    ) -> Intervention | None:
        """Apply ordered intervention rules."""

        # Rule 0: Brain dump reminder — only when idle/unfocused and not in a task
        if (
            self._brain_dump_reminders
            and self._brain_dump_reminders.has_pending()
            and self._brain_dump_reminders.time_since_oldest() >= 5.0
            and metrics.behavioral_state in ("idle", "distracted", "multitasking")
            and metrics.focus_score < 30
        ):
            reminder = self._brain_dump_reminders.pop_next()
            if reminder:
                minutes_ago = (datetime.now() - reminder.captured_at.replace(tzinfo=None)).total_seconds() / 60
                time_label = f"{int(minutes_ago)}m ago" if minutes_ago < 60 else f"{int(minutes_ago / 60)}h ago"
                return Intervention(
                    type="brain_dump_reminder",
                    ef_domain="self_motivation",
                    acknowledgment=f"Remember this? \"{reminder.content_preview}\"",
                    suggestion=f"Captured {time_label}. Your mind seems free — want to come back to this?",
                    actions=[
                        InterventionAction(id="brain_dump", emoji="🧠", label="Open Brain Dump"),
                        InterventionAction(id="later", emoji="⏰", label="Remind me later"),
                        InterventionAction(id="dismiss", emoji="✕", label="Not now"),
                    ],
                    requires_senticnet=False,
                    notification_tier=2,
                    urgency_color="green",
                )

        # Rule 1: Distraction spiral (Self-restraint deficit)
        if (
            metrics.context_switch_rate_5min > 12
            and metrics.distraction_ratio > 0.5
        ):
            return Intervention(
                type="distraction_spiral",
                ef_domain="self_restraint",
                acknowledgment="Looks like things are scattered right now — that's okay.",
                suggestion="A 2-minute reset could help you refocus. What feels right?",
                actions=[
                    InterventionAction(id="breathe", emoji="🫁", label="Breathing exercise"),
                    InterventionAction(id="task_pick", emoji="🎯", label="Pick one task"),
                    InterventionAction(id="break", emoji="☕", label="Take a break"),
                ],
                requires_senticnet=False,
            )

        # Rule 2: Sustained disengagement (Self-motivation deficit)
        if (
            metrics.behavioral_state == "distracted"
            and metrics.current_streak_minutes > 20
            and metrics.distraction_ratio > 0.7
        ):
            return Intervention(
                type="sustained_disengagement",
                ef_domain="self_motivation",
                acknowledgment="It's been a while since your last focused stretch.",
                suggestion="Sometimes the hardest part is just starting. What's the smallest step you could take?",
                actions=[
                    InterventionAction(id="tiny_task", emoji="🪜", label="5-min micro-task"),
                    InterventionAction(id="body_double", emoji="👥", label="Find a body double"),
                    InterventionAction(id="reward_first", emoji="🎁", label="Set a reward"),
                ],
                requires_senticnet=False,
            )

        # Rule 3: Hyperfocus on wrong task (Self-management to time)
        if metrics.hyperfocus_detected:
            return Intervention(
                type="hyperfocus_check",
                ef_domain="self_management_time",
                acknowledgment="You've been deeply focused for 3+ hours — that's impressive focus!",
                suggestion="Quick check: is this the most important thing right now?",
                actions=[
                    InterventionAction(id="yes_continue", emoji="✅", label="Yes, keep going"),
                    InterventionAction(id="switch_task", emoji="🔄", label="Switch to priority"),
                    InterventionAction(id="time_box", emoji="⏰", label="Set 30min timer"),
                ],
                requires_senticnet=False,
            )

        # Rule 4: Emotional escalation (Self-regulation of emotion)
        if emotion_context and emotion_context.get("emotional_dysregulation"):
            return Intervention(
                type="emotional_escalation",
                ef_domain="self_regulation_emotion",
                acknowledgment="Things seem intense right now. That's a valid feeling.",
                suggestion="Would any of these help you process what you're feeling?",
                actions=[
                    InterventionAction(id="vent", emoji="💬", label="Vent to me"),
                    InterventionAction(id="ground", emoji="🌿", label="Grounding exercise"),
                    InterventionAction(id="walk", emoji="🚶", label="Take a walk"),
                ],
                requires_senticnet=True,
            )

        return None

    def _wellbeing_check_intervention(
        self, metrics: ADHDMetrics, now: datetime,
    ) -> Intervention:
        """4+ hour wellbeing check — the only exception for productive hyperfocus."""
        intervention = Intervention(
            type="hyperfocus_wellbeing",
            ef_domain="self_management_time",
            acknowledgment="You've been in the zone for over 4 hours — incredible focus!",
            suggestion="Your body might appreciate a quick check-in.",
            actions=[
                InterventionAction(id="water", emoji="💧", label="Hydrate"),
                InterventionAction(id="stretch", emoji="🧘", label="Quick stretch"),
                InterventionAction(id="continue", emoji="▶️", label="I'm good"),
            ],
            requires_senticnet=False,
            notification_tier=3,
            urgency_color="green",
        )
        self._intervention_count_this_block += 1
        self._last_intervention_time = now
        return intervention

    # ── Private helpers ──────────────────────────────────────────────

    def _is_in_cooldown(self, now: datetime) -> bool:
        if self._last_intervention_time is None:
            return False
        elapsed = (now - self._last_intervention_time).total_seconds()
        return elapsed < self._cooldown_seconds

    def _minutes_since_last(self, now: datetime) -> float:
        if self._last_intervention_time is None:
            return 999.0
        return (now - self._last_intervention_time).total_seconds() / 60

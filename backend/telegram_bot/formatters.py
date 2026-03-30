"""Plain-text message formatters for Telegram — ADHD-friendly, no MarkdownV2."""

from models.insights import CurrentInsights, WeeklyInsights
from models.whoop_data import MorningBriefing, RecoveryTier


def format_morning_briefing(briefing: MorningBriefing) -> str:
    """Format morning briefing by recovery tier.

    Green  -> Energized, deep work encouraged
    Yellow -> Moderate, structured pacing
    Red    -> Low energy, gentle tasks
    """
    tier = briefing.recovery_tier
    score = briefing.recovery_score
    focus_min = briefing.recommended_focus_block_minutes

    if tier == RecoveryTier.GREEN:
        header = f"Good morning! Recovery: {score}% (Green)"
        body = (
            f"Great recovery — today is optimal for deep, challenging work.\n"
            f"Recommended focus blocks: {focus_min} minutes\n"
        )
    elif tier == RecoveryTier.YELLOW:
        header = f"Good morning! Recovery: {score}% (Yellow)"
        body = (
            f"Moderate recovery — use structured pacing with extra scaffolding.\n"
            f"Recommended focus blocks: {focus_min} minutes\n"
        )
    else:
        header = f"Good morning! Recovery: {score}% (Red)"
        body = (
            f"Low recovery — stick to easy tasks, frequent breaks, and written lists.\n"
            f"Recommended focus blocks: {focus_min} minutes\n"
        )

    stats = (
        f"\nHRV: {briefing.hrv_rmssd:.0f}ms  |  Resting HR: {briefing.resting_hr:.0f}bpm\n"
        f"Deep sleep: {briefing.sws_percentage:.0f}%  |  REM: {briefing.rem_percentage:.0f}%"
    )

    notes = ""
    if briefing.sleep_notes:
        notes = "\n\nHeads up:\n" + "\n".join(f"  - {n}" for n in briefing.sleep_notes)

    return f"{header}\n\n{body}{stats}{notes}"


def format_focus_check(current: CurrentInsights) -> str:
    """Format current behavioral state as a focus check."""
    state = current.behavioral_state
    app = current.current_app or "nothing"
    category = current.current_category or "unknown"

    if state == "focused":
        return (
            f"You're focused right now on {app} ({category}).\n\n"
            "Nice flow! Keep going — I'll check in later."
        )
    elif state == "distracted":
        return (
            f"Looks like you've been bouncing around — currently on {app} ({category}).\n\n"
            "No judgment. Pick ONE thing and give it 10 minutes."
        )
    elif state == "hyperfocused":
        return (
            f"You've been locked in on {app} for a while.\n\n"
            "Hyperfocus is a superpower, but check: have you had water? "
            "Stretched? Take 2 minutes, then dive back in."
        )
    elif state == "multitasking":
        return (
            f"You're switching between apps a lot — currently on {app}.\n\n"
            "ADHD brains love novelty, but deep work needs single-tasking. "
            "Close the extra tabs and pick one."
        )
    elif state == "idle":
        return (
            "Looks like you're away from the screen.\n\n"
            "When you're back, start with something small to build momentum."
        )
    else:
        return (
            f"Current state: {state} (on {app})\n\n"
            "How are you feeling? Send me a message if you want to talk it through."
        )


def format_weekly_review(weekly: WeeklyInsights) -> str:
    """Format weekly insights with trend analysis."""
    trend = weekly.trend
    avg_focus = weekly.avg_focus_percentage
    avg_distraction = weekly.avg_distraction_percentage

    if trend == "improving":
        header = "Weekly Review: Things are improving!"
        insight = "Your focus has been trending upward this week. Whatever you're doing, keep at it."
    elif trend == "declining":
        header = "Weekly Review: A tougher week"
        insight = (
            "Focus dipped compared to earlier in the week. "
            "That's okay — ADHD isn't linear. What felt hardest?"
        )
    else:
        header = "Weekly Review: Holding steady"
        insight = "Consistent week. Stability is underrated with ADHD."

    stats = (
        f"\nAvg focus: {avg_focus:.0f}%  |  Avg distraction: {avg_distraction:.0f}%"
    )

    if weekly.best_focus_day:
        stats += f"\nBest focus day: {weekly.best_focus_day}"
    if weekly.worst_focus_day:
        stats += f"\nHardest day: {weekly.worst_focus_day}"

    top_apps = ""
    if weekly.top_apps_weekly:
        top_apps = "\n\nTop apps this week:\n" + "\n".join(
            f"  {a.app_name}: {a.minutes:.0f} min ({a.percentage:.0f}%)"
            for a in weekly.top_apps_weekly[:3]
        )

    interventions = ""
    if weekly.total_interventions > 0:
        interventions = (
            f"\n\nInterventions: {weekly.total_interventions} triggered, "
            f"{weekly.intervention_acceptance_rate:.0f}% accepted"
        )

    return f"{header}\n\n{insight}{stats}{top_apps}{interventions}"

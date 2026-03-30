"""Handler for /focus command and scheduled focus check."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from services.insights_service import InsightsService
from telegram_bot.formatters import format_focus_check

logger = logging.getLogger("adhd-brain.telegram.focus")

FALLBACK_MESSAGE = (
    "Focus check:\n\n"
    "Pick ONE task right now. Set a 10-minute timer.\n"
    "Just 10 minutes — you can do anything for 10 minutes."
)

# Scheduled job only fires during active hours
ACTIVE_HOUR_START = 9
ACTIVE_HOUR_END = 22


async def focus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /focus — current behavioral state check."""
    try:
        insights = InsightsService()
        current = insights.get_current()
        text = format_focus_check(current)
    except Exception as e:
        logger.error(f"Focus check failed: {e}")
        text = FALLBACK_MESSAGE
        await update.message.reply_text(text)
        raise

    await update.message.reply_text(text)


async def scheduled_focus_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback — sends focus nudge only when warranted.

    Gates:
    - Active hours only (9 AM - 10 PM)
    - Only sends if distracted (ratio > 0.5) or hyperfocused (streak > 180 min)
    """
    now = datetime.now()
    if now.hour < ACTIVE_HOUR_START or now.hour >= ACTIVE_HOUR_END:
        return

    chat_id = context.job.data

    try:
        insights = InsightsService()
        current = insights.get_current()
    except Exception as e:
        logger.error(f"Scheduled focus check failed: {e}")
        await context.bot.send_message(chat_id=chat_id, text=FALLBACK_MESSAGE)
        return

    # Gate: only send if distracted or hyperfocused
    state = current.behavioral_state
    metrics = current.metrics

    should_send = False
    if state == "distracted":
        distraction_ratio = metrics.get("distraction_ratio", 0)
        if distraction_ratio > 0.5:
            should_send = True
    elif state == "hyperfocused":
        focus_streak_min = metrics.get("focus_streak_seconds", 0) / 60
        if focus_streak_min > 180:
            should_send = True

    if not should_send:
        return

    text = format_focus_check(current)
    await context.bot.send_message(chat_id=chat_id, text=text)

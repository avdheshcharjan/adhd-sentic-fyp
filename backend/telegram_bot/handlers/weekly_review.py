"""Handler for /weekly command and scheduled weekly review."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.insights_service import InsightsService
from telegram_bot.formatters import format_weekly_review

logger = logging.getLogger("adhd-brain.telegram.weekly")

FALLBACK_MESSAGE = (
    "Weekly review:\n\n"
    "Take a moment to reflect on what went well this week.\n"
    "What helped you focus? What got in the way?\n"
    "One small adjustment for next week is enough."
)


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weekly — 7-day trend review."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        insights = InsightsService()
        weekly = await insights.get_weekly()
        text = format_weekly_review(weekly)
    except Exception as e:
        logger.error(f"Weekly review failed: {e}")
        text = FALLBACK_MESSAGE
        await update.message.reply_text(text)
        raise

    await update.message.reply_text(text)


async def scheduled_weekly_review(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback — sends weekly review on Sunday evening."""
    chat_id = context.job.data
    try:
        insights = InsightsService()
        weekly = await insights.get_weekly()
        text = format_weekly_review(weekly)
    except Exception as e:
        logger.error(f"Scheduled weekly review failed: {e}")
        text = FALLBACK_MESSAGE

    await context.bot.send_message(chat_id=chat_id, text=text)

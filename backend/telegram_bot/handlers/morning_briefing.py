"""Handler for /morning command and scheduled morning briefing."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.whoop_service import WhoopService
from telegram_bot.formatters import format_morning_briefing

logger = logging.getLogger("adhd-brain.telegram.morning")

FALLBACK_MESSAGE = (
    "Good morning!\n\n"
    "Couldn't fetch your Whoop data right now.\n\n"
    "Default plan: Start with 25-minute focus blocks and check in with "
    "yourself every hour. You've got this."
)


async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /morning — fetch and send morning briefing."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        whoop = WhoopService()
        briefing = await whoop.generate_morning_briefing()
        text = format_morning_briefing(briefing)
    except Exception as e:
        logger.error(f"Morning briefing failed: {e}")
        text = FALLBACK_MESSAGE
        await update.message.reply_text(text)
        raise

    await update.message.reply_text(text)


async def scheduled_morning_briefing(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback — sends morning briefing to configured chat."""
    chat_id = context.job.data
    try:
        whoop = WhoopService()
        briefing = await whoop.generate_morning_briefing()
        text = format_morning_briefing(briefing)
    except Exception as e:
        logger.error(f"Scheduled morning briefing failed: {e}")
        text = FALLBACK_MESSAGE

    await context.bot.send_message(chat_id=chat_id, text=text)

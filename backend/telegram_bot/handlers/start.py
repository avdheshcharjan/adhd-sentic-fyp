"""Handler for /start and /help commands."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger("adhd-brain.telegram.start")

WELCOME_TEXT = (
    "Welcome to ADHD Second Brain\n\n"
    "I'm your personal ADHD coaching companion. Here's what I can do:\n\n"
    "Just text me — Vent or chat about anything. I'll listen and respond with "
    "ADHD-aware coaching.\n\n"
    "Commands:\n"
    "/morning — Get your morning briefing (Whoop recovery + focus plan)\n"
    "/focus — Check your current focus state\n"
    "/weekly — Weekly review with trends and insights\n"
    "/help — Show this message\n\n"
    "Scheduled messages:\n"
    "  7:30 AM — Morning briefing\n"
    "  Every 30 min (9AM-10PM) — Focus nudge (only when needed)\n"
    "  Sunday 8 PM — Weekly review\n"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome message + log chat_id."""
    chat_id = update.effective_chat.id
    logger.info(f"Telegram /start from chat_id={chat_id}")
    await update.message.reply_text(
        f"{WELCOME_TEXT}\nYour chat ID: {chat_id}\n"
        "Add this as TELEGRAM_CHAT_ID in your .env for scheduled messages."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — same as /start."""
    await update.message.reply_text(WELCOME_TEXT)

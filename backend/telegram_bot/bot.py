"""Telegram bot application factory — builds and configures but does NOT start."""

import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram_bot.handlers.start import start_command, help_command
from telegram_bot.handlers.vent import vent_handler, action_button_callback
from telegram_bot.handlers.morning_briefing import morning_command
from telegram_bot.handlers.focus_check import focus_command
from telegram_bot.handlers.weekly_review import weekly_command
from telegram_bot.scheduler import register_scheduled_jobs

logger = logging.getLogger("adhd-brain.telegram")


def create_bot_application(token: str) -> Application:
    """Build a configured Telegram bot Application.

    The caller is responsible for calling:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

    And on shutdown:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

    Args:
        token: Telegram bot API token.

    Returns:
        Configured Application (not yet started).
    """
    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("morning", morning_command))
    application.add_handler(CommandHandler("focus", focus_command))
    application.add_handler(CommandHandler("weekly", weekly_command))

    # Callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(action_button_callback))

    # Default text handler — all non-command text goes to vent pipeline
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, vent_handler)
    )

    # Register scheduled jobs (morning briefing, focus checks, weekly review)
    register_scheduled_jobs(application)

    logger.info("Telegram bot application configured")
    return application

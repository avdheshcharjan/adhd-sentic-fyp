"""Cron job registration using python-telegram-bot JobQueue."""

import logging
from datetime import time

from telegram.ext import Application

from config import get_settings
from telegram_bot.handlers.morning_briefing import scheduled_morning_briefing
from telegram_bot.handlers.focus_check import scheduled_focus_check
from telegram_bot.handlers.weekly_review import scheduled_weekly_review

logger = logging.getLogger("adhd-brain.telegram.scheduler")


def register_scheduled_jobs(application: Application) -> None:
    """Register all cron/repeating jobs on the bot's JobQueue.

    Jobs only run if TELEGRAM_CHAT_ID is configured. Without it,
    the bot still works for on-demand commands but won't push messages.
    """
    settings = get_settings()
    chat_id = settings.TELEGRAM_CHAT_ID

    if not chat_id:
        logger.warning(
            "TELEGRAM_CHAT_ID not set — scheduled messages disabled. "
            "Send /start to the bot to get your chat ID."
        )
        return

    job_queue = application.job_queue

    # Morning briefing — daily at 7:30 AM
    job_queue.run_daily(
        scheduled_morning_briefing,
        time=time(hour=7, minute=30),
        data=chat_id,
        name="morning_briefing",
    )
    logger.info("Scheduled: morning briefing at 07:30 daily")

    # Focus check — every 30 minutes (handler gates active hours 9AM-10PM)
    job_queue.run_repeating(
        scheduled_focus_check,
        interval=1800,  # 30 minutes
        data=chat_id,
        name="focus_check",
    )
    logger.info("Scheduled: focus check every 30 min (active 9AM-10PM)")

    # Weekly review — Sunday at 8 PM (day 6 = Sunday)
    job_queue.run_daily(
        scheduled_weekly_review,
        time=time(hour=20, minute=0),
        days=(6,),
        data=chat_id,
        name="weekly_review",
    )
    logger.info("Scheduled: weekly review at 20:00 on Sundays")

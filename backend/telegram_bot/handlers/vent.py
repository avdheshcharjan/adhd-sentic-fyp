"""Default text handler — routes all non-command messages through the vent pipeline."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services.chat_processor import ChatProcessor
from services.action_suggestions import get_suggested_actions
from services.constants import CRISIS_RESPONSE_TEXT, CRISIS_RESOURCES_SG

logger = logging.getLogger("adhd-brain.telegram.vent")

_processor = ChatProcessor()

# Action button response templates
ACTION_RESPONSES: dict[str, str] = {
    "breathe": (
        "Breathing exercise:\n\n"
        "1. Breathe in for 4 counts\n"
        "2. Hold for 4 counts\n"
        "3. Breathe out for 6 counts\n\n"
        "Repeat 3 times. You've got this."
    ),
    "continue": "I'm here. Tell me what's on your mind.",
    "break": (
        "Take 5 minutes away from your screen.\n"
        "Stand up, stretch, get water.\n"
        "Your brain needs the reset."
    ),
    "smallest_step": (
        "What's ONE tiny thing you could do in the next 2 minutes?\n"
        "Not the whole task — just the smallest possible step."
    ),
}


async def vent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process any text message through the full vent pipeline."""
    text = update.message.text
    chat_id = update.effective_chat.id
    conversation_id = f"telegram_{chat_id}"

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        result = await _processor.process_vent_message(
            text=text,
            conversation_id=conversation_id,
            user_id=conversation_id,
        )
    except Exception as e:
        logger.error(f"Vent pipeline error: {e}")
        await update.message.reply_text(
            "Something went wrong processing your message.\n\n"
            "If you need support right now:\n"
            + "\n".join(f"  {r['label']}" for r in CRISIS_RESOURCES_SG)
        )
        raise

    if not result["used_llm"]:
        # Crisis mode — send resources
        crisis_text = CRISIS_RESPONSE_TEXT + "\n\n" + "\n".join(
            f"  {r['label']}" for r in CRISIS_RESOURCES_SG
        )
        await update.message.reply_text(crisis_text)
        return

    # Build inline keyboard from suggested actions
    actions = get_suggested_actions(result)
    keyboard = [
        [InlineKeyboardButton(a["label"], callback_data=a["id"])]
        for a in actions
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(result["response"], reply_markup=reply_markup)


async def action_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses from vent responses."""
    query = update.callback_query
    await query.answer()

    action_id = query.data
    response = ACTION_RESPONSES.get(
        action_id,
        "I'm here whenever you need me. Just send a message.",
    )
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(response)

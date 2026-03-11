"""
Chat/venting endpoint — full SenticNet pipeline integration.
Runs the 4-tier affective computing pipeline on user messages.
"""

from fastapi import APIRouter

from models.chat_message import ChatInput, ChatResponse
from services.senticnet_pipeline import SenticNetPipeline

router = APIRouter(prefix="/chat", tags=["chat"])

# ── Singleton pipeline ──────────────────────────────────
_pipeline = SenticNetPipeline()


@router.post("/message", response_model=ChatResponse)
async def process_message(message: ChatInput):
    """
    Process a venting/chat message through the SenticNet pipeline.

    Pipeline:
      1. Safety check (depression, toxicity, intensity)
      2. Emotion analysis (emotion, polarity, subjectivity, sarcasm)
      3. ADHD signal derivation (engagement, wellbeing, concepts, aspects)
      4. Deep analysis (personality, ensemble) — full mode only
    """
    # Run the full SenticNet pipeline
    result = await _pipeline.analyze(text=message.text, mode="full")

    # Build response with safety check
    if result.safety.is_critical:
        response_text = (
            "I hear you, and I want you to know that what you're feeling matters. "
            "If you're in crisis, please reach out to the 988 Suicide & Crisis Lifeline "
            "(call or text 988). You don't have to go through this alone."
        )
    elif result.safety.level == "high":
        response_text = (
            f"I can sense you're going through a really tough time. "
            f"Your feelings are valid. "
            f"Would it help to talk to someone who can offer more support?"
        )
    else:
        emotion = result.emotion.primary_emotion
        response_text = (
            f"I'm picking up on {emotion} in what you're saying. "
            f"That's completely understandable. "
            f"Would you like to explore what's behind this, "
            f"or would a quick reset activity help more right now?"
        )

    return ChatResponse(
        response=response_text,
        emotion_profile=result.emotion.model_dump() if result.emotion else None,
        safety_flags=result.safety.model_dump() if result.safety else None,
        suggested_actions=_get_suggested_actions(result),
    )


def _get_suggested_actions(result) -> list[dict] | None:
    """Generate suggested actions based on SenticNet analysis."""
    actions = []

    if result.safety.is_critical:
        return [
            {"id": "crisis_call", "emoji": "📞", "label": "Call 988 Lifeline"},
            {"id": "crisis_text", "emoji": "💬", "label": "Text HOME to 741741"},
            {"id": "crisis_talk", "emoji": "🤝", "label": "Talk to someone I trust"},
        ]

    if result.adhd_signals.is_overwhelmed:
        actions.append({"id": "breathe", "emoji": "🫁", "label": "2-minute breathing exercise"})
        actions.append({"id": "braindump", "emoji": "📝", "label": "Brain dump — write everything down"})

    if result.adhd_signals.is_disengaged:
        actions.append({"id": "smallest_step", "emoji": "🎯", "label": "Pick the smallest possible next step"})
        actions.append({"id": "timer_5min", "emoji": "⏰", "label": "Set a 5-minute timer to just start"})

    if result.adhd_signals.is_frustrated:
        actions.append({"id": "break", "emoji": "☕", "label": "Take a short break"})
        actions.append({"id": "switch_task", "emoji": "🔄", "label": "Switch to a different task"})

    if result.adhd_signals.emotional_dysregulation:
        actions.append({"id": "grounding", "emoji": "🧊", "label": "Grounding: name 5 things you can see"})

    if not actions:
        actions = [
            {"id": "pick_task", "emoji": "🎯", "label": "Pick a task"},
            {"id": "breathe", "emoji": "🫁", "label": "Quick breathing"},
            {"id": "break", "emoji": "☕", "label": "Take a break"},
        ]

    return actions

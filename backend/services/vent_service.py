"""
Vent chat service — on-device LLM with 4-layer safety system.

Safety layers:
  Layer 1: Keyword-based crisis detection
  Layer 2: SenticNet semantic crisis detection (polarity + intensity)
  Layer 3: Output safety check (post-generation)
  Layer 4: Session-level escalation tracking (worsening polarity trend)
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import AsyncGenerator

from services.memory_service import MemoryService
from services.mlx_inference import MLXInference
from services.senticnet_pipeline import SenticNetPipeline

logger = logging.getLogger("adhd-brain.vent")


# Layer 1: Crisis keywords (exact substring match)
CRISIS_KEYWORDS = [
    "kill myself", "want to die", "end my life", "suicide",
    "self-harm", "hurt myself", "don't want to be alive",
    "better off dead", "no reason to live", "can't go on",
    "end it all", "take my life",
]

CRISIS_RESPONSE = (
    "What you're going through sounds really painful, and I want to make sure you get "
    "the right support. Please reach out to the 988 Suicide & Crisis Lifeline (call or text 988) "
    "or Crisis Text Line (text HOME to 741741). You deserve real human support right now.\n\n"
    "I'm here if you want to talk about anything else, but for what you're going through "
    "right now, a real person can help in ways I can't."
)

# Layer 3: Output safety — patterns that should not appear in LLM output
UNSAFE_OUTPUT_PATTERNS = [
    "you should take",     # medication advice
    "stop taking",         # medication advice
    "your dose",           # medication advice
    "you're right, you",   # agreeing with self-deprecation
    "i diagnose",          # diagnosing
    "you have depression", # diagnosing
    "you have anxiety",    # diagnosing
]

SAFE_FALLBACK = (
    "I hear you, and what you're feeling is valid. Want to tell me more about what's going on?"
)

# Layer 4: Escalation nudge (not a hard stop, just a gentle resource reminder)
ESCALATION_NUDGE = (
    "It sounds like things are feeling heavier. If you're going through something really "
    "difficult, talking to someone who can truly help could make a big difference — "
    "988 Lifeline is always available (call or text 988). No pressure at all."
)


class VentService:
    """Manages vent chat sessions with on-device LLM inference and 4-layer safety."""

    def __init__(
        self,
        llm: MLXInference,
        senticnet: SenticNetPipeline,
        memory: MemoryService,
    ):
        self.llm = llm
        self.senticnet = senticnet
        self.memory = memory
        self.system_prompt = self._load_system_prompt()

        # Layer 4: Per-session polarity tracking {session_id: [polarity_scores]}
        self._session_polarities: dict[str, list[float]] = defaultdict(list)

    def _load_system_prompt(self) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / "vent_system_prompt.txt"
        return prompt_path.read_text()

    # ── Layer 1: Keyword crisis detection ─────────────────────────────

    def check_crisis_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CRISIS_KEYWORDS)

    # ── Layer 2: SenticNet semantic crisis detection ──────────────────

    def check_crisis_semantic(self, safety_level: str) -> bool:
        """Triggers when SenticNet safety tier reports critical or high."""
        return safety_level in ("critical", "high")

    # ── Layer 3: Output safety check ──────────────────────────────────

    def check_output_safety(self, response: str) -> bool:
        """Returns True if the response is SAFE. False if it should be replaced."""
        response_lower = response.lower()
        return not any(pattern in response_lower for pattern in UNSAFE_OUTPUT_PATTERNS)

    # ── Layer 4: Session escalation tracking ──────────────────────────

    def track_polarity(self, session_id: str, polarity_score: float) -> bool:
        """Track polarity and return True if escalation nudge should fire.

        Fires when 3 consecutive messages show worsening (more negative) polarity.
        """
        history = self._session_polarities[session_id]
        history.append(polarity_score)

        if len(history) < 3:
            return False

        last_three = history[-3:]
        # Each successive message is more negative than the previous
        return last_three[0] > last_three[1] > last_three[2] and last_three[2] < -0.3

    # ── Main entry point ──────────────────────────────────────────────

    async def stream_response(
        self,
        message: str,
        session_id: str,
        history: list[dict],
    ) -> AsyncGenerator[str, None]:
        """Yields response tokens with full 4-layer safety."""

        # Layer 1: Keyword crisis check
        if self.check_crisis_keywords(message):
            yield CRISIS_RESPONSE
            return

        # SenticNet emotion analysis (lightweight mode for speed)
        emotion_context: str | None = None
        polarity_score: float = 0.0
        safety_level: str = "normal"

        try:
            result = await self.senticnet.analyze(message, mode="full")
            primary_emotion = result.emotion.primary_emotion
            polarity_score = result.emotion.polarity_score
            safety_level = result.safety.level
            emotion_context = (
                f"Dominant emotion: {primary_emotion} "
                f"(polarity: {polarity_score:.2f}, "
                f"intensity: {result.adhd_signals.intensity_score:.0f}/100)"
            )
        except Exception as e:
            logger.warning(f"SenticNet analysis failed for vent: {e}")

        # Layer 2: Semantic crisis check
        if self.check_crisis_semantic(safety_level):
            yield CRISIS_RESPONSE
            return

        # Layer 4: Track polarity for escalation detection
        needs_escalation_nudge = self.track_polarity(session_id, polarity_score)

        # Build messages for LLM
        messages = self._build_messages(message, history, emotion_context)

        # Generate response via MLX (synchronous — run in thread)
        full_response = await self._generate_response(messages)

        # Layer 3: Output safety check
        if not self.check_output_safety(full_response):
            logger.warning(f"Unsafe output detected in vent response, using fallback")
            yield SAFE_FALLBACK
            return

        # Yield the full response (MLX generate is not token-streaming capable)
        yield full_response

        # Layer 4: Append escalation nudge if needed
        if needs_escalation_nudge:
            yield f"\n\n{ESCALATION_NUDGE}"

        # Store interaction in Mem0 (non-blocking, best-effort)
        try:
            self.memory.add_conversation_memory(
                user_id="default_user",
                message=f"User: {message}\nAssistant: {full_response}",
                context=f"vent_session|{session_id}|{primary_emotion if emotion_context else 'unknown'}",
            )
        except Exception as e:
            logger.warning(f"Failed to store vent interaction in Mem0: {e}")

    def _build_messages(
        self,
        user_message: str,
        history: list[dict],
        emotion_context: str | None = None,
    ) -> list[dict]:
        """Assemble the full message list for LLM inference."""
        system_content = self.system_prompt

        if emotion_context:
            system_content += (
                f"\n\n[Emotion context — do not reveal to user] "
                f"The user's message shows: {emotion_context}. "
                f"Calibrate your response accordingly."
            )

        # Build conversation for the LLM's context
        # We pass system prompt + recent history + current message as a single prompt
        # since MLX generate_coaching_response expects system_prompt + user_message
        conversation_context = ""
        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_context += f"\n{role.capitalize()}: {content}"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"{conversation_context}\nUser: {user_message}" if conversation_context else user_message},
        ]

    async def _generate_response(self, messages: list[dict]) -> str:
        """Generate LLM response using MLX (runs synchronously in thread pool)."""
        import asyncio

        system_prompt = messages[0]["content"]
        user_message = messages[1]["content"]

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.llm.generate_coaching_response(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=512,
                temperature=0.7,
                use_thinking=False,
            ),
        )
        return response

    def clear_session(self, session_id: str) -> None:
        """Clear session state when user starts a new session."""
        self._session_polarities.pop(session_id, None)

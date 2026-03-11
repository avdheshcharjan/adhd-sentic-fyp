# Phase 7: On-Device LLM Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add on-device LLM coaching via Qwen3-4B on Apple MLX, upgrade the activity classifier with embedding-based Layer 4, and wire the full chat pipeline (SenticNet -> safety -> LLM -> Mem0).

**Architecture:** Three new services: `mlx_inference.py` (model lifecycle), `chat_processor.py` (orchestration pipeline), `constants.py` (prompts/resources). Modified files: `config.py` (MLX settings), `requirements.txt` (new deps), `main.py` (background cleanup), `chat.py` (wire chat_processor), `activity_classifier.py` (Layer 4 embeddings), `chat_message.py` (new response fields).

**Tech Stack:** mlx-lm (Apple MLX), sentence-transformers (all-MiniLM-L6-v2), Qwen3-4B-4bit, FastAPI, Pydantic v2

---

### Task 1: Add MLX Dependencies to requirements.txt

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add new dependencies**

Add after the `psycopg` line (before the Testing section):

```
mlx-lm>=0.31.0
sentence-transformers>=3.0.0
numpy>=1.26.0
```

**Step 2: Install dependencies**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw && pip install -r backend/requirements.txt`
Expected: All packages install successfully. mlx-lm pulls in mlx framework.

**Step 3: Verify imports**

Run: `python -c "import mlx_lm; import sentence_transformers; import numpy; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat(phase7): add mlx-lm, sentence-transformers, numpy dependencies"
```

---

### Task 2: Add MLX Settings to config.py

**Files:**
- Modify: `backend/config.py:36-38`

**Step 1: Add MLX configuration fields**

After the existing `OPENAI_API_KEY` line (line 38), add:

```python
    # ── MLX On-Device LLM ─────────────────────────────────
    MLX_PRIMARY_MODEL: str = "mlx-community/Qwen3-4B-4bit"
    MLX_LIGHT_MODEL: str = "mlx-community/Qwen3-1.7B-4bit"
    MLX_ADAPTER_PATH: str | None = None  # LoRA adapter path (optional)
    MLX_KEEP_ALIVE_SECONDS: int = 120  # Unload LLM after 2 min idle
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # For classification Layer 4
```

**Step 2: Verify config loads**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from config import get_settings; s = get_settings(); print(s.MLX_PRIMARY_MODEL, s.MLX_KEEP_ALIVE_SECONDS)"`
Expected: `mlx-community/Qwen3-4B-4bit 120`

**Step 3: Commit**

```bash
git add backend/config.py
git commit -m "feat(phase7): add MLX model config settings"
```

---

### Task 3: Create constants.py (System Prompt + Crisis Resources)

**Files:**
- Create: `backend/services/constants.py`

**Step 1: Write the constants file**

```python
"""
Constants for the ADHD coaching system.
System prompt, crisis resources, and shared configuration.
"""

# Singapore crisis resources (from blueprint Section 12)
CRISIS_RESOURCES_SG = [
    {"id": "sos_caretext", "label": "SOS CareText: 1-767-4357"},
    {"id": "imh_hotline", "label": "IMH Helpline: 6389-2222"},
    {"id": "national_care", "label": "National Care Hotline: 1800-202-6868"},
]

CRISIS_RESPONSE_TEXT = (
    "I hear you, and I want you to know that what you're feeling matters. "
    "If things feel really heavy right now, these people are trained to help:"
)

# Default ADHD coaching system prompt (from models.md)
ADHD_COACHING_SYSTEM_PROMPT = """You are an empathetic ADHD coach inside a personal "Second Brain" application.

CORE RULES:
1. Under 2-3 sentences per response (ADHD working memory is limited)
2. ALWAYS validate the emotion before suggesting anything ("I hear you" before "Try this")
3. Maximum 2-3 choices when offering options (decision fatigue)
4. Use upward framing ("A 3-min reset helps 72% of the time" NOT "You've been distracted for an hour")
5. Never guilt, shame, or compare to neurotypical standards
6. If the user is in crisis (safety_level=critical), ONLY show compassion + crisis resources. Do NOT coach.

COMMUNICATION STYLE:
- Warm but not patronizing
- Brief but not dismissive
- Acknowledge the difficulty of having ADHD without making it the user's entire identity
- Use "and" instead of "but" when connecting validation to suggestions

You receive structured emotional data from SenticNet (an emotion AI system) in your context.
Use this data to understand how the user is feeling — but NEVER mention SenticNet or scores to the user.
Speak naturally, as if you simply understand them."""
```

**Step 2: Verify import**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from services.constants import ADHD_COACHING_SYSTEM_PROMPT, CRISIS_RESOURCES_SG; print(len(ADHD_COACHING_SYSTEM_PROMPT), len(CRISIS_RESOURCES_SG))"`
Expected: Two numbers (prompt length and 3)

**Step 3: Commit**

```bash
git add backend/services/constants.py
git commit -m "feat(phase7): add ADHD coaching system prompt and SG crisis resources"
```

---

### Task 4: Create mlx_inference.py (LLM Lifecycle Manager)

**Files:**
- Create: `backend/services/mlx_inference.py`
- Test: `backend/tests/test_mlx_inference.py`

**Step 1: Write the failing test**

```python
"""Tests for MLX inference service."""

import time
from unittest.mock import patch, MagicMock
from services.mlx_inference import MLXInference


class TestMLXInferenceLifecycle:
    """Test model load/unload lifecycle without actual model files."""

    def test_initial_state_is_unloaded(self):
        inference = MLXInference()
        assert inference.model is None
        assert inference.tokenizer is None
        assert inference.current_model_key is None

    def test_unload_when_already_unloaded_is_safe(self):
        inference = MLXInference()
        inference._unload()  # Should not raise
        assert inference.model is None

    def test_maybe_unload_when_no_model_is_noop(self):
        inference = MLXInference()
        inference.maybe_unload_if_idle()  # Should not raise
        assert inference.model is None

    @patch("services.mlx_inference.load")
    def test_load_model_sets_state(self, mock_load):
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)

        inference = MLXInference()
        inference._load_model("primary")

        assert inference.model is mock_model
        assert inference.tokenizer is mock_tokenizer
        assert inference.current_model_key == "primary"
        assert inference.last_used is not None

    @patch("services.mlx_inference.load")
    def test_load_same_model_twice_is_noop(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")
        inference._load_model("primary")  # Same key — should skip

        mock_load.assert_called_once()

    @patch("services.mlx_inference.load")
    def test_unload_frees_model(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")
        inference._unload()

        assert inference.model is None
        assert inference.tokenizer is None
        assert inference.current_model_key is None

    @patch("services.mlx_inference.load")
    def test_maybe_unload_respects_ttl(self, mock_load):
        mock_load.return_value = (MagicMock(), MagicMock())

        inference = MLXInference()
        inference._load_model("primary")

        # Just loaded — should NOT unload
        inference.maybe_unload_if_idle()
        assert inference.model is not None

    @patch("services.mlx_inference.load")
    def test_generate_loads_model_on_demand(self, mock_load):
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "formatted prompt"
        mock_load.return_value = (mock_model, mock_tokenizer)

        with patch("services.mlx_inference.generate", return_value="I hear you."):
            inference = MLXInference()
            result = inference.generate_coaching_response(
                system_prompt="You are a coach.",
                user_message="I feel overwhelmed.",
            )

        assert result == "I hear you."
        assert inference.model is not None  # Was loaded on demand
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_mlx_inference.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.mlx_inference'`

**Step 3: Write mlx_inference.py**

```python
"""
On-device LLM inference using Apple MLX framework.
Load-on-demand architecture for 16GB M4 Mac.

Primary: Qwen3-4B Instruct 4-bit (~2.3 GB) — loaded when coaching needed
Fallback: Qwen3-1.7B 4-bit (~1.1 GB) — lighter option if memory pressure detected
"""

import gc
import logging
import time
from datetime import datetime
from typing import Optional

from mlx_lm import load, generate

from config import get_settings

settings = get_settings()
logger = logging.getLogger("adhd-brain.mlx")


class MLXInference:
    """
    Manages on-device LLM lifecycle: load -> generate -> unload.

    Memory pattern on 16GB M4:
    - Classifier (all-MiniLM-L6-v2, ~80MB) -> always resident
    - Coaching LLM (Qwen3-4B, ~2.3GB) -> load on demand, unload after TTL
    - SenticNet (HTTP client, ~50MB) -> always resident
    Peak AI memory: ~2.5 GB. Leaves 3-5 GB headroom.
    """

    MODELS = {
        "primary": settings.MLX_PRIMARY_MODEL,
        "light": settings.MLX_LIGHT_MODEL,
    }

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.current_model_key: Optional[str] = None
        self.last_used: Optional[datetime] = None

    def _load_model(self, model_key: str = "primary"):
        """Load model into unified memory. ~2-5s on M4 SSD."""
        if self.current_model_key == model_key:
            return

        self._unload()

        model_id = self.MODELS[model_key]
        start = time.time()

        kwargs = {"path_or_hf_repo": model_id}
        if settings.MLX_ADAPTER_PATH:
            kwargs["adapter_path"] = settings.MLX_ADAPTER_PATH

        self.model, self.tokenizer = load(**kwargs)
        load_time = time.time() - start

        self.current_model_key = model_key
        self.last_used = datetime.now()
        logger.info(f"Loaded {model_id} in {load_time:.1f}s")

    def _unload(self):
        """Free model memory. Essential on 16GB machine."""
        if self.model is not None:
            model_key = self.current_model_key
            self.model = None
            self.tokenizer = None
            self.current_model_key = None
            gc.collect()
            logger.info(f"Model {model_key} unloaded, memory freed")

    def maybe_unload_if_idle(self):
        """Called periodically by background task. Unloads after TTL."""
        if self.model is None or self.last_used is None:
            return

        idle_seconds = (datetime.now() - self.last_used).total_seconds()
        if idle_seconds > settings.MLX_KEEP_ALIVE_SECONDS:
            logger.info(f"Model idle for {idle_seconds:.0f}s, unloading")
            self._unload()

    def generate_coaching_response(
        self,
        system_prompt: str,
        user_message: str,
        senticnet_context: dict | None = None,
        whoop_context: dict | None = None,
        adhd_profile_context: dict | None = None,
        max_tokens: int = 250,
        temperature: float = 0.7,
        use_thinking: bool = False,
    ) -> str:
        """
        Generate an ADHD-aware coaching response.

        SenticNet provides pre-computed emotional context (the hard part).
        The LLM generates natural, empathetic text given that context (the easy part).
        """
        self._load_model("primary")
        self.last_used = datetime.now()

        # Build context sections
        context_parts = []

        if senticnet_context:
            context_parts.append(
                f"<senticnet_analysis>\n"
                f"Primary emotion: {senticnet_context.get('primary_emotion', 'unknown')}\n"
                f"Intensity: {senticnet_context.get('intensity_score', 0):.0f}/100\n"
                f"Engagement: {senticnet_context.get('engagement_score', 0):.0f}/100\n"
                f"Well-being: {senticnet_context.get('wellbeing_score', 0):.0f}/100\n"
                f"Safety level: {senticnet_context.get('safety_level', 'normal')}\n"
                f"Key concepts: {', '.join(senticnet_context.get('concepts', [])[:5])}\n"
                f"ADHD state: {senticnet_context.get('primary_adhd_state', 'neutral')}\n"
                f"</senticnet_analysis>"
            )

        if whoop_context:
            context_parts.append(
                f"<whoop_data>\n"
                f"Recovery: {whoop_context.get('recovery_score', 'unknown')}% "
                f"({whoop_context.get('recovery_tier', 'unknown')})\n"
                f"HRV: {whoop_context.get('hrv_rmssd', 'unknown')}ms\n"
                f"Sleep performance: {whoop_context.get('sleep_performance', 'unknown')}%\n"
                f"</whoop_data>"
            )

        if adhd_profile_context:
            context_parts.append(
                f"<adhd_profile>\n"
                f"Subtype: {adhd_profile_context.get('subtype', 'unspecified')}\n"
                f"Severity: {adhd_profile_context.get('severity', 'unknown')}\n"
                f"Medicated: {adhd_profile_context.get('is_medicated', False)}\n"
                f"</adhd_profile>"
            )

        context_section = "\n".join(context_parts)

        # Qwen3 thinking mode prefix
        thinking_prefix = "/think\n" if use_thinking else "/no_think\n"

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{context_section}"},
            {"role": "user", "content": f"{thinking_prefix}{user_message}"},
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature,
        )

        return response

    def generate_morning_briefing(
        self,
        whoop_data: dict,
        adhd_profile: dict,
        yesterday_summary: dict | None = None,
    ) -> str:
        """Generate a personalized ADHD morning briefing from Whoop data."""
        system_prompt = (
            "You are a supportive ADHD coach delivering a morning briefing.\n"
            "Rules:\n"
            "- Under 5 sentences total\n"
            "- Start with energy/mood acknowledgment based on recovery data\n"
            "- Give ONE specific, actionable recommendation for today\n"
            "- Use warm, encouraging tone (never clinical or robotic)\n"
            "- If recovery is low, emphasize self-compassion over productivity"
        )

        whoop_summary = (
            f"Recovery: {whoop_data.get('recovery_score', '?')}% "
            f"({whoop_data.get('recovery_tier', '?')})\n"
            f"Sleep: {whoop_data.get('sleep_performance', '?')}%\n"
            f"HRV: {whoop_data.get('hrv_rmssd', '?')}ms\n"
            f"Recommended focus blocks: "
            f"{whoop_data.get('recommended_focus_block_minutes', 25)} minutes"
        )

        return self.generate_coaching_response(
            system_prompt=system_prompt,
            user_message=f"Generate my morning briefing:\n{whoop_summary}",
            adhd_profile_context=adhd_profile,
            use_thinking=False,
            max_tokens=200,
            temperature=0.6,
        )


# Singleton instance
mlx_inference = MLXInference()
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_mlx_inference.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add backend/services/mlx_inference.py backend/tests/test_mlx_inference.py
git commit -m "feat(phase7): add MLX inference service with load-on-demand lifecycle"
```

---

### Task 5: Update ChatResponse Model

**Files:**
- Modify: `backend/models/chat_message.py`

**Step 1: Add new fields to ChatResponse**

Add `used_llm` and `thinking_mode` fields:

```python
"""Pydantic models for chat/venting messages."""

from pydantic import BaseModel


class ChatInput(BaseModel):
    """Input from OpenClaw or Dashboard chat."""

    text: str
    conversation_id: str | None = None
    context: dict | None = None


class ChatResponse(BaseModel):
    """Response with LLM reply + optional emotional analysis."""

    response: str
    emotion_profile: dict | None = None
    safety_flags: dict | None = None
    suggested_actions: list[dict] | None = None
    used_llm: bool = False
    thinking_mode: str | None = None
```

**Step 2: Verify model**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from models.chat_message import ChatResponse; r = ChatResponse(response='hi', used_llm=True, thinking_mode='no_think'); print(r.model_dump())"`
Expected: Dict with all fields including `used_llm: True` and `thinking_mode: 'no_think'`

**Step 3: Commit**

```bash
git add backend/models/chat_message.py
git commit -m "feat(phase7): add used_llm and thinking_mode to ChatResponse"
```

---

### Task 6: Create chat_processor.py (Full Chat Pipeline)

**Files:**
- Create: `backend/services/chat_processor.py`
- Test: `backend/tests/test_chat_processor.py`

**Step 1: Write the failing test**

```python
"""Tests for chat processor pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.chat_processor import ChatProcessor


@pytest.fixture
def processor():
    """Create ChatProcessor with mocked dependencies."""
    with patch("services.chat_processor.SenticNetPipeline") as mock_pipeline_cls, \
         patch("services.chat_processor.mlx_inference") as mock_mlx, \
         patch("services.chat_processor.memory_service") as mock_mem:

        mock_pipeline = AsyncMock()
        mock_pipeline_cls.return_value = mock_pipeline

        proc = ChatProcessor()
        proc.pipeline = mock_pipeline
        proc._mlx = mock_mlx
        proc._memory = mock_mem

        yield proc, mock_pipeline, mock_mlx, mock_mem


def _make_senticnet_result(is_critical=False, safety_level="normal",
                            primary_emotion="neutral", intensity=0.0,
                            engagement=0.0, wellbeing=0.0):
    """Helper to build a mock SenticNetResult."""
    result = MagicMock()
    result.safety.is_critical = is_critical
    result.safety.level = safety_level
    result.safety.depression_score = 0.0
    result.safety.toxicity_score = 0.0
    result.safety.intensity_score = intensity
    result.emotion.primary_emotion = primary_emotion
    result.emotion.introspection = 0.0
    result.emotion.temper = 0.0
    result.emotion.attitude = 0.0
    result.emotion.sensitivity = 0.0
    result.adhd_signals.intensity_score = intensity
    result.adhd_signals.engagement_score = engagement
    result.adhd_signals.wellbeing_score = wellbeing
    result.adhd_signals.concepts = ["work", "stress"]
    result.adhd_signals.is_overwhelmed = False
    result.adhd_signals.is_disengaged = False
    result.adhd_signals.is_frustrated = False
    result.adhd_signals.emotional_dysregulation = False
    return result


class TestChatProcessorSafety:
    @pytest.mark.asyncio
    async def test_critical_safety_returns_crisis_resources_no_llm(self, processor):
        proc, mock_pipeline, mock_mlx, mock_mem = processor
        mock_pipeline.analyze.return_value = _make_senticnet_result(
            is_critical=True, safety_level="critical"
        )

        result = await proc.process_vent_message("I want to end it all")

        assert result["used_llm"] is False
        assert "resources" in result
        assert len(result["resources"]) == 3  # SG crisis resources
        mock_mlx.generate_coaching_response.assert_not_called()


class TestChatProcessorLLM:
    @pytest.mark.asyncio
    async def test_normal_message_uses_llm(self, processor):
        proc, mock_pipeline, mock_mlx, mock_mem = processor
        mock_pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="frustration", intensity=40.0
        )
        mock_mlx.generate_coaching_response.return_value = "I hear your frustration."

        result = await proc.process_vent_message("I can't focus on anything today")

        assert result["used_llm"] is True
        assert result["response"] == "I hear your frustration."
        mock_mlx.generate_coaching_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_high_intensity_uses_think_mode(self, processor):
        proc, mock_pipeline, mock_mlx, mock_mem = processor
        mock_pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="anger", intensity=75.0
        )
        mock_mlx.generate_coaching_response.return_value = "That sounds really tough."

        result = await proc.process_vent_message("Everything is falling apart")

        assert result["thinking_mode"] == "think"
        call_kwargs = mock_mlx.generate_coaching_response.call_args[1]
        assert call_kwargs["use_thinking"] is True

    @pytest.mark.asyncio
    async def test_low_intensity_uses_no_think_mode(self, processor):
        proc, mock_pipeline, mock_mlx, mock_mem = processor
        mock_pipeline.analyze.return_value = _make_senticnet_result(
            primary_emotion="boredom", intensity=20.0
        )
        mock_mlx.generate_coaching_response.return_value = "Let's find something engaging."

        result = await proc.process_vent_message("Meh")

        assert result["thinking_mode"] == "no_think"


class TestChatProcessorMemory:
    @pytest.mark.asyncio
    async def test_stores_conversation_in_memory(self, processor):
        proc, mock_pipeline, mock_mlx, mock_mem = processor
        mock_pipeline.analyze.return_value = _make_senticnet_result()
        mock_mlx.generate_coaching_response.return_value = "I'm here for you."

        await proc.process_vent_message("I feel stuck")

        mock_mem.add_conversation_memory.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_chat_processor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.chat_processor'`

**Step 3: Write chat_processor.py**

```python
"""
Full chat processing pipeline.

SenticNet detects emotion (hard part) -> LLM generates response (easy part).
Safety check is non-negotiable and runs FIRST.
"""

import logging
from typing import Optional

from services.senticnet_pipeline import SenticNetPipeline
from services.mlx_inference import mlx_inference
from services.memory_service import memory_service
from services.constants import (
    ADHD_COACHING_SYSTEM_PROMPT,
    CRISIS_RESOURCES_SG,
    CRISIS_RESPONSE_TEXT,
)

logger = logging.getLogger("adhd-brain.chat")


class ChatProcessor:
    """Orchestrates the full chat pipeline: SenticNet -> Safety -> LLM -> Memory."""

    def __init__(self):
        self.pipeline = SenticNetPipeline()
        self._mlx = mlx_inference
        self._memory = memory_service

    async def process_vent_message(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        user_id: str = "default_user",
    ) -> dict:
        """
        Full pipeline for processing a user's venting/chat message.

        1. SenticNet analysis (fast, deterministic)
        2. Safety check (non-negotiable, runs FIRST)
        3. Build structured context for LLM
        4. Determine /think vs /no_think mode
        5. Generate response via MLX
        6. Store in Mem0
        """
        # Step 1: SenticNet analysis
        result = await self.pipeline.analyze(text=text, mode="full")

        # Step 2: Safety check — critical = no LLM, just compassion + resources
        if result.safety.is_critical:
            return {
                "response": CRISIS_RESPONSE_TEXT,
                "resources": CRISIS_RESOURCES_SG,
                "senticnet": self._build_senticnet_context(result),
                "used_llm": False,
                "thinking_mode": None,
            }

        # Step 3: Build structured context
        senticnet_context = self._build_senticnet_context(result)

        # Step 4: Determine thinking mode
        use_thinking = (
            abs(result.adhd_signals.intensity_score) > 60
            or "help" in text.lower()
            or len(text) > 200
        )

        # Step 5: Generate response via MLX
        response = self._mlx.generate_coaching_response(
            system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
            user_message=text,
            senticnet_context=senticnet_context,
            use_thinking=use_thinking,
        )

        # Step 6: Store in memory
        try:
            self._memory.add_conversation_memory(
                user_id=user_id,
                message=f"User: {text}\nAssistant: {response}",
                context=str(senticnet_context),
            )
        except Exception as e:
            logger.warning(f"Failed to store conversation memory: {e}")

        return {
            "response": response,
            "senticnet": senticnet_context,
            "used_llm": True,
            "thinking_mode": "think" if use_thinking else "no_think",
        }

    def _build_senticnet_context(self, result) -> dict:
        """Extract structured context from SenticNetResult for LLM injection."""
        return {
            "primary_emotion": result.emotion.primary_emotion,
            "introspection": result.emotion.introspection,
            "temper": result.emotion.temper,
            "attitude": result.emotion.attitude,
            "sensitivity": result.emotion.sensitivity,
            "intensity_score": result.adhd_signals.intensity_score,
            "engagement_score": result.adhd_signals.engagement_score,
            "wellbeing_score": result.adhd_signals.wellbeing_score,
            "safety_level": result.safety.level,
            "concepts": result.adhd_signals.concepts[:5],
        }
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_chat_processor.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add backend/services/chat_processor.py backend/tests/test_chat_processor.py
git commit -m "feat(phase7): add chat processor pipeline (SenticNet -> LLM -> Mem0)"
```

---

### Task 7: Wire chat_processor into /chat/message Endpoint

**Files:**
- Modify: `backend/api/chat.py` (full rewrite)

**Step 1: Replace chat.py with chat_processor integration**

```python
"""
Chat/venting endpoint — full pipeline: SenticNet -> Safety -> LLM -> Memory.
"""

from fastapi import APIRouter

from models.chat_message import ChatInput, ChatResponse
from services.chat_processor import ChatProcessor
from services.constants import CRISIS_RESOURCES_SG

router = APIRouter(prefix="/chat", tags=["chat"])

_processor = ChatProcessor()


@router.post("/message", response_model=ChatResponse)
async def process_message(message: ChatInput):
    """
    Process a venting/chat message through the full pipeline.

    Pipeline:
      1. SenticNet emotion analysis
      2. Safety check (crisis -> resources, no LLM)
      3. Qwen3-4B coaching response via MLX
      4. Mem0 memory storage
    """
    result = await _processor.process_vent_message(
        text=message.text,
        conversation_id=message.conversation_id,
    )

    # Build suggested actions from SenticNet context
    suggested_actions = _get_suggested_actions(result)

    return ChatResponse(
        response=result["response"],
        emotion_profile=result.get("senticnet"),
        safety_flags=None,
        suggested_actions=suggested_actions,
        used_llm=result["used_llm"],
        thinking_mode=result.get("thinking_mode"),
    )


def _get_suggested_actions(result: dict) -> list[dict]:
    """Generate suggested actions based on pipeline result."""
    if not result["used_llm"]:
        # Crisis mode — show SG crisis resources as actions
        return [
            {"id": r["id"], "label": r["label"]}
            for r in CRISIS_RESOURCES_SG
        ]

    senticnet = result.get("senticnet", {})
    intensity = abs(senticnet.get("intensity_score", 0))
    engagement = senticnet.get("engagement_score", 0)

    actions = []
    if intensity > 60:
        actions.append({"id": "breathe", "label": "2-minute breathing exercise"})
    if engagement < -30:
        actions.append({"id": "smallest_step", "label": "Pick the smallest next step"})
    if intensity < -50:
        actions.append({"id": "break", "label": "Take a short break"})

    if not actions:
        actions = [
            {"id": "continue", "label": "Tell me more"},
            {"id": "breathe", "label": "Quick breathing"},
            {"id": "break", "label": "Take a break"},
        ]

    return actions[:3]  # Never more than 3 choices (ADHD constraint)
```

**Step 2: Verify endpoint still conforms to ChatResponse model**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from api.chat import router; print('Chat router loaded OK')"`
Expected: `Chat router loaded OK`

**Step 3: Commit**

```bash
git add backend/api/chat.py
git commit -m "feat(phase7): wire chat_processor into /chat/message endpoint"
```

---

### Task 8: Add Background Model Cleanup to main.py

**Files:**
- Modify: `backend/main.py:7-9` and `backend/main.py:40-57`

**Step 1: Add asyncio import and MLX import**

Add `import asyncio` after the existing `logging` import (line 8), and add the mlx_inference import after the memory_service import (line 26):

```python
from services.mlx_inference import mlx_inference
```

**Step 2: Add cleanup task and update lifespan**

Replace the lifespan function with:

```python
async def _model_cleanup_loop():
    """Periodically check if LLM should be unloaded to free memory."""
    while True:
        try:
            mlx_inference.maybe_unload_if_idle()
        except Exception as e:
            logger.warning(f"Model cleanup error: {e}")
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    logger.info("ADHD Second Brain starting up...")
    logger.info(f"   Version : {settings.APP_VERSION}")
    logger.info(f"   Port    : {settings.APP_PORT}")

    # Init database schema
    logger.info("Initializing PostgreSQL schema...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified.")

    # Start background model cleanup
    cleanup_task = asyncio.create_task(_model_cleanup_loop())
    logger.info("Background model cleanup task started (30s interval)")

    yield

    cleanup_task.cancel()
    mlx_inference._unload()
    logger.info("ADHD Second Brain shutting down...")
```

**Step 3: Verify app starts**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from main import app; print('App created OK')"`
Expected: `App created OK`

**Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat(phase7): add background model cleanup task to lifespan"
```

---

### Task 9: Upgrade Activity Classifier with Layer 4 Embeddings

**Files:**
- Modify: `backend/services/activity_classifier.py`
- Modify: `backend/tests/test_activity_classifier.py`

**Step 1: Write new Layer 4 tests**

Add to the existing test file:

```python
class TestL4EmbeddingSimilarity:
    """Test Layer 4 zero-shot embedding classification."""

    def test_ambiguous_title_gets_classified(self):
        """An ambiguous title that L1-L3 can't handle should get a real category."""
        c = _classifier()
        category, layer = c.classify(
            "SomeRandomApp",
            "Implementing binary search algorithm in Python"
        )
        # Embedding similarity should recognize this as development
        assert category == "development"
        assert layer == 4

    def test_low_confidence_returns_other(self):
        """Completely nonsensical input should return 'other'."""
        c = _classifier()
        category, layer = c.classify(
            "SomeRandomApp",
            "asdfghjkl qwerty zxcvbn"
        )
        assert category == "other"
        assert layer == 4


class TestUserCorrections:
    """Test user correction cache (Layer 0)."""

    def test_correction_overrides_all_layers(self):
        c = _classifier()
        # First classify normally
        cat1, _ = c.classify("Google Chrome", "YouTube - Music")
        assert cat1 == "entertainment"

        # User corrects: this is actually research
        c.record_correction("Google Chrome", "YouTube - Music", "research")

        # Now classification should return research
        cat2, layer = c.classify("Google Chrome", "YouTube - Music")
        assert cat2 == "research"
        assert layer == 0  # User correction layer
```

**Step 2: Run tests to verify new tests fail**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_activity_classifier.py::TestL4EmbeddingSimilarity -v`
Expected: FAIL (Layer 4 currently returns "other" for everything)

**Step 3: Update activity_classifier.py**

Replace the full file with the upgraded version that adds:
- `numpy` and `sentence_transformers` imports
- `CATEGORY_DESCRIPTIONS` dict for zero-shot similarity
- `_embedding_model` and `_category_embeddings` lazy-loaded fields
- `_ensure_embedding_model()` method
- User correction cache: `user_corrections` dict, `record_correction()`, `load_corrections_from_db()`
- Layer 0 (corrections) before Layer 1 in `classify()`
- Layer 4 uses embedding similarity instead of returning "other"
- Return value changes: `tuple[str, int]` now includes confidence via layer number, and layer 0 for corrections

```python
"""
4-layer Activity Classifier for the ADHD Second Brain system.

Classification pipeline:
  L0: User corrections     (highest priority, instant)
  L1: App name lookup      (~70% coverage, <1ms)
  L2: URL domain lookup    (~20% coverage, <1ms)
  L3: Window title keywords (~8% coverage, <2ms)
  L4: Embedding similarity  (~2%, <25ms, all-MiniLM-L6-v2)
"""

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

logger = logging.getLogger("adhd-brain.classifier")

# ── Constants ───────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

VALID_CATEGORIES = {
    "development", "writing", "research", "communication",
    "social_media", "entertainment", "news", "shopping",
    "productivity", "design", "finance", "browser", "system", "other",
}

# L3 — keyword -> category mapping for window title heuristics
TITLE_KEYWORDS: dict[str, str] = {
    "youtube": "entertainment",
    "netflix": "entertainment",
    "twitch": "entertainment",
    "spotify": "entertainment",
    "disney+": "entertainment",
    "reddit": "social_media",
    "twitter": "social_media",
    "instagram": "social_media",
    "tiktok": "social_media",
    "facebook": "social_media",
    "github": "development",
    "gitlab": "development",
    "stack overflow": "development",
    "pull request": "development",
    "localhost": "development",
    "terminal": "development",
    "amazon": "shopping",
    "shopee": "shopping",
    "cart": "shopping",
    "checkout": "shopping",
    "bbc": "news",
    "cnn": "news",
    "reuters": "news",
    "breaking news": "news",
    "notion": "productivity",
    "todoist": "productivity",
    "trello": "productivity",
    "trading": "finance",
    "coinmarketcap": "finance",
    "binance": "finance",
    "robinhood": "finance",
    "arxiv": "research",
    "scholar": "research",
    "wikipedia": "research",
    "pubmed": "research",
}

# Category descriptions for Layer 4 zero-shot embedding similarity
CATEGORY_DESCRIPTIONS = {
    "development": "Programming, coding, software development, debugging, terminal, IDE, code editor, GitHub, pull request, repository",
    "writing": "Writing documents, essays, reports, notes, drafting text, word processing, blogging, LaTeX, Overleaf",
    "research": "Academic research, reading papers, Wikipedia, scholarly articles, learning, studying, arxiv, library",
    "communication": "Email, messaging, video calls, chat, Slack, Teams, meetings, correspondence, Discord",
    "social_media": "Social media browsing, Twitter, Instagram, Reddit, TikTok, Facebook, LinkedIn feed, scrolling",
    "entertainment": "Watching videos, streaming, gaming, music, YouTube, Netflix, Twitch, Spotify, anime",
    "news": "Reading news articles, current events, BBC, CNN, news websites, journalism, headlines",
    "shopping": "Online shopping, browsing products, Amazon, Shopee, Lazada, comparing prices, e-commerce, cart",
    "design": "Graphic design, UI design, Figma, Sketch, Photoshop, illustration, prototyping, wireframe",
    "productivity": "Task management, calendars, to-do lists, project management, Notion, spreadsheets, Obsidian",
}


class ActivityClassifier:
    """
    Classifies screen activity into productivity categories using a 5-layer pipeline.

    Layer 0: User corrections (highest priority, instant)
    Layer 1: App name lookup (~70% of cases, <0.01ms)
    Layer 2: URL domain lookup (~20% of browser cases, <0.01ms)
    Layer 3: Window title keywords (~8% of remaining, <0.1ms)
    Layer 4: Zero-shot embedding similarity (~2% fallback, <25ms)
    """

    def __init__(self) -> None:
        self._app_categories = self._load_json("app_categories.json")
        self._url_categories = self._load_json("url_categories.json")
        self._embedding_model = None
        self._category_embeddings = None
        self.user_corrections: dict[str, str] = {}

    # ── Public API ──────────────────────────────────────────────────

    def classify(
        self,
        app_name: str,
        window_title: str,
        url: str | None = None,
    ) -> tuple[str, int]:
        """
        Classify the current screen activity.

        Returns:
            (category, layer) — the matched category and which layer matched (0-4).
        """
        # L0: User corrections (highest priority)
        correction_key = f"{app_name}|{window_title}".strip().lower()
        if correction_key in self.user_corrections:
            return self.user_corrections[correction_key], 0

        # L1: App name lookup
        category = self._classify_by_app(app_name)
        if category and category != "browser":
            return category, 1

        # L2: URL domain lookup (only if URL is provided)
        if url:
            category = self._classify_by_url(url)
            if category:
                return category, 2

        # L3: Window title keyword matching
        category = self._classify_by_title(window_title)
        if category:
            return category, 3

        # If app was classified as "browser" but no URL/title match, return browser
        if self._classify_by_app(app_name) == "browser":
            return "browser", 1

        # L4: Zero-shot embedding similarity
        return self._classify_by_embedding(app_name, window_title)

    def record_correction(self, app_name: str, window_title: str, correct_category: str):
        """User corrects a misclassification. Takes effect immediately."""
        key = f"{app_name}|{window_title}".strip().lower()
        self.user_corrections[key] = correct_category

    def load_corrections_from_db(self, corrections: dict[str, str]):
        """Load persisted corrections on startup."""
        self.user_corrections = corrections

    # ── Private methods ─────────────────────────────────────────────

    def _ensure_embedding_model(self):
        """Lazy-load sentence transformer only when needed (Layer 4 fallback)."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._category_embeddings = self._embedding_model.encode(
                list(CATEGORY_DESCRIPTIONS.values()),
                normalize_embeddings=True,
            )
            logger.info("Loaded all-MiniLM-L6-v2 for Layer 4 classification")

    def _classify_by_embedding(self, app_name: str, window_title: str) -> tuple[str, int]:
        """L4: Zero-shot embedding similarity. <25ms on M4."""
        self._ensure_embedding_model()
        title_embedding = self._embedding_model.encode(
            f"{app_name}: {window_title}",
            normalize_embeddings=True,
        )
        similarities = np.dot(self._category_embeddings, title_embedding)
        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])
        category_names = list(CATEGORY_DESCRIPTIONS.keys())

        if confidence > 0.35:
            return category_names[best_idx], 4

        return "other", 4

    def _classify_by_app(self, app_name: str) -> str | None:
        """L1: Direct app name lookup."""
        return self._app_categories.get(app_name)

    def _classify_by_url(self, url: str) -> str | None:
        """L2: Domain extraction + lookup with parent-domain fallback."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return None

            category = self._url_categories.get(hostname)
            if category:
                return category

            if hostname.startswith("www."):
                hostname = hostname[4:]
                category = self._url_categories.get(hostname)
                if category:
                    return category

            parts = hostname.split(".")
            if len(parts) > 2:
                parent = ".".join(parts[-2:])
                category = self._url_categories.get(parent)
                if category:
                    return category

            return None
        except Exception:
            return None

    def _classify_by_title(self, window_title: str) -> str | None:
        """L3: Keyword matching in window title (case-insensitive)."""
        title_lower = window_title.lower()
        for keyword, category in TITLE_KEYWORDS.items():
            if keyword in title_lower:
                return category
        return None

    def _load_json(self, filename: str) -> dict:
        """Load a JSON knowledge base file."""
        filepath = KNOWLEDGE_DIR / filename
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Knowledge base not found: {filepath}")
            return {}
```

**Step 4: Run all classifier tests**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/test_activity_classifier.py -v`
Expected: All existing tests PASS + new Layer 4 and correction tests PASS

**Step 5: Commit**

```bash
git add backend/services/activity_classifier.py backend/tests/test_activity_classifier.py
git commit -m "feat(phase7): add Layer 4 embedding similarity and user corrections to classifier"
```

---

### Task 10: Run Full Test Suite and Verify

**Files:**
- No new files

**Step 1: Run all backend tests**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 2: Verify app imports cleanly**

Run: `cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw/backend && python -c "from main import app; print('All imports OK, app ready')"`
Expected: `All imports OK, app ready`

**Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "feat(phase7): complete on-device LLM integration"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Add MLX dependencies | `requirements.txt` |
| 2 | Add MLX config settings | `config.py` |
| 3 | Create constants (prompt + crisis resources) | `services/constants.py` |
| 4 | Create MLX inference service | `services/mlx_inference.py` + test |
| 5 | Update ChatResponse model | `models/chat_message.py` |
| 6 | Create chat processor pipeline | `services/chat_processor.py` + test |
| 7 | Wire chat_processor into endpoint | `api/chat.py` |
| 8 | Add background cleanup to main.py | `main.py` |
| 9 | Upgrade classifier with embeddings | `services/activity_classifier.py` + test |
| 10 | Run full test suite | verification |

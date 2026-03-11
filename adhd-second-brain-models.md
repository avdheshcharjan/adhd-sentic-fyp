# ADHD Second Brain — AI Model & Inference Specification
## Consolidated LLM, Classification, and Fine-Tuning Plan for Claude Code

> **Companion to**: `adhd-second-brain-blueprint.md` + `adhd-second-brain-supplement.md` + `architecture-diagram.mermaid`
> **Purpose**: This document REPLACES all model-related decisions in the blueprint (Section 7: mlx_inference.py, config.py MLX settings, and the activity classifier's Layer 4).
> **Hardware target**: MacBook Pro M4 base, 16GB unified memory, 120 GB/s bandwidth, 10-core GPU

---

## EXECUTIVE SUMMARY: WHAT CHANGED AND WHY

The original blueprint specified a single `Llama-3.2-3B-Instruct-4bit` model for both activity classification and ADHD coaching. This is wrong for three reasons:

1. **Using a 3B generative LLM to classify window titles is like hiring a surgeon to take a temperature.** A 22M-parameter sentence transformer does it 10× faster at 1/40th the memory.

2. **Llama 3.2 3B has been surpassed.** Qwen3-4B matches Qwen2.5-7B quality in the same memory envelope, with dual thinking modes specifically suited to ADHD coaching.

3. **16GB M4 can't keep an LLM resident permanently.** After macOS and user apps, only ~5-7GB remains. The LLM must load on-demand and unload when idle.

**The new architecture splits into three layers:**

| Layer | Model | Memory | Latency | Runs |
|-------|-------|--------|---------|------|
| Classification | Rules + `all-MiniLM-L6-v2` | ~80 MB | <25ms | Always-on |
| Emotion detection | SenticNet Python API + REST APIs | ~50 MB | <5ms | Always-on |
| Coaching LLM | Qwen3-4B 4-bit (+ LoRA adapter) | ~2.3 GB | 30-40 tok/s | On-demand |
| **Total peak** | | **~2.5 GB** | | |

This leaves **3-5 GB headroom** even during heavy multitasking.

---

## 1. ACTIVITY CLASSIFICATION (REPLACES BLUEPRINT SECTION 6.2 LAYER 4)

### Architecture: 4-Layer Cascade — NO LLM INVOLVED

The classification pipeline uses zero ML models for 98% of cases, and a tiny sentence transformer for the remaining 2%. No generative LLM is ever used for classification.

**File: `backend/services/activity_classifier.py`** (COMPLETE REPLACEMENT)

```python
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

# Load static dictionaries at module level
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
APP_CATEGORIES = json.loads((_KNOWLEDGE_DIR / "app_categories.json").read_text())
URL_CATEGORIES = json.loads((_KNOWLEDGE_DIR / "url_categories.json").read_text())

class ActivityClassifier:
    """
    4-layer activity classifier. NO generative LLM used at any layer.

    Layer 1: App name lookup (JSON dict)           — ~70% of cases, <0.01ms
    Layer 2: URL domain lookup (JSON dict)          — ~20% of browser cases, <0.01ms
    Layer 3: Window title keywords (substring match) — ~8% of remaining, <0.1ms
    Layer 4: Zero-shot embedding similarity          — ~2% fallback, <25ms
           + User correction cache                   — instant for corrected titles

    Total memory: ~80MB (sentence transformer) + negligible (dicts)
    """

    # Category descriptions for zero-shot embedding similarity
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

    # Keyword rules for Layer 3
    KEYWORD_RULES = {
        "development": ["vscode", "terminal", "github", "stack overflow", "localhost", "debug", "pull request", "npm", "pip", "docker", "git"],
        "writing": ["docs.google", "notion.so", "word", "overleaf", "grammarly", "draft", "essay", "report"],
        "communication": ["mail", "gmail", "outlook", "slack", "teams", "discord", "zoom", "meet", "telegram", "whatsapp"],
        "social_media": ["twitter", "x.com", "instagram", "facebook", "reddit", "tiktok", "linkedin feed", "threads"],
        "entertainment": ["youtube", "netflix", "spotify", "twitch", "gaming", "steam", "crunchyroll", "disney+"],
        "research": ["arxiv", "scholar", "pubmed", "wikipedia", "library", "ieee", "springer", "sciencedirect"],
        "news": ["news", "bbc", "cnn", "nytimes", "guardian", "reuters", "straits times", "channelnewsasia"],
        "design": ["figma", "sketch", "photoshop", "canva", "dribbble", "behance"],
        "shopping": ["amazon", "shopee", "lazada", "ebay", "aliexpress", "cart", "checkout"],
    }

    def __init__(self):
        # Layer 4: Sentence transformer for zero-shot classification
        # all-MiniLM-L6-v2: 22M params, ~80MB, <25ms per classification on M4
        self._embedding_model = None  # Lazy load — only if Layers 1-3 fail
        self._category_embeddings = None

        # User correction cache (persisted to SQLite between sessions)
        self.user_corrections: dict[str, str] = {}

    def _ensure_embedding_model(self):
        """Lazy-load sentence transformer only when needed (Layer 4 fallback)."""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self._category_embeddings = self._embedding_model.encode(
                list(self.CATEGORY_DESCRIPTIONS.values()),
                normalize_embeddings=True
            )

    def classify(self, app_name: str, window_title: str, url: str | None) -> tuple[str, float]:
        """
        Classify current activity. Returns (category, confidence).
        Confidence: 1.0 for rule-based matches, 0.0-1.0 for embedding similarity.
        """
        # Layer 0: User corrections (highest priority, instant)
        correction_key = f"{app_name}|{window_title}".strip().lower()
        if correction_key in self.user_corrections:
            return self.user_corrections[correction_key], 1.0

        # Layer 1: App name lookup (~70% of cases)
        app_lower = app_name.lower()
        if app_lower in APP_CATEGORIES:
            category = APP_CATEGORIES[app_lower]
            if category != "browser":  # Browsers need URL/title analysis
                return category, 1.0

        # Layer 2: URL domain lookup (~20% of browser cases)
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            if domain in URL_CATEGORIES:
                return URL_CATEGORIES[domain], 0.95
            # Check parent domain
            parts = domain.split(".")
            if len(parts) > 2:
                parent = ".".join(parts[-2:])
                if parent in URL_CATEGORIES:
                    return URL_CATEGORIES[parent], 0.9

        # Layer 3: Window title keywords (~8% of remaining)
        title_lower = window_title.lower()
        for category, keywords in self.KEYWORD_RULES.items():
            if any(kw in title_lower for kw in keywords):
                return category, 0.85

        # Layer 4: Zero-shot embedding similarity (~2% fallback)
        self._ensure_embedding_model()
        title_embedding = self._embedding_model.encode(
            f"{app_name}: {window_title}",
            normalize_embeddings=True
        )
        similarities = np.dot(self._category_embeddings, title_embedding)
        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])
        category_names = list(self.CATEGORY_DESCRIPTIONS.keys())

        if confidence > 0.35:
            return category_names[best_idx], confidence

        return "other", 0.0

    def record_correction(self, app_name: str, window_title: str, correct_category: str):
        """User corrects a misclassification. Persisted to SQLite."""
        key = f"{app_name}|{window_title}".strip().lower()
        self.user_corrections[key] = correct_category

    def load_corrections_from_db(self, corrections: dict[str, str]):
        """Load persisted corrections on startup."""
        self.user_corrections = corrections
```

### User Correction API Endpoint

**Add to `backend/api/screen.py`:**
```python
@router.post("/correct-category")
async def correct_category(app_name: str, window_title: str, correct_category: str):
    """
    User corrects a misclassified activity via right-click menu.
    Stored locally in SQLite. Takes effect immediately.
    """
    activity_classifier.record_correction(app_name, window_title, correct_category)
    # Persist to SQLite
    await db.execute(
        "INSERT OR REPLACE INTO user_corrections (key, category) VALUES (?, ?)",
        (f"{app_name}|{window_title}".strip().lower(), correct_category)
    )
    return {"status": "corrected", "category": correct_category}
```

### How Per-User Personalization Works (No Fine-Tuning)

```
Ships with app (shared):              Grows per-user over time:
├── app_categories.json (300+ apps)   ├── user_corrections.json
├── url_categories.json (500+ domains)│   ("Untitled - Figma" → "design")
├── keyword_rules (in code)           ├── user_app_overrides.json
├── all-MiniLM-L6-v2 (80MB)          │   ("Obsidian" → "research" not "productivity")
└── Qwen3-4B + LoRA adapter          ├── user_priority_apps.json
                                      └── personal_baseline.json (14-day calibration)
```

After a few days of occasional right-click corrections, the system handles 99%+ of each user's apps correctly. No model retraining needed. Same pattern Rize and ActivityWatch use.

---

## 2. COACHING LLM (REPLACES BLUEPRINT SECTION 7: mlx_inference.py)

### Why Qwen3-4B, Not Llama 3.2 3B

| Factor | Llama 3.2 3B | Qwen3-4B | Winner |
|--------|-------------|----------|--------|
| Quality | Matches Llama 2 7B | Matches Qwen2.5-7B | Qwen3 |
| Empathy | ⭐⭐⭐ adequate | ⭐⭐⭐⭐ strong | Qwen3 |
| Dual mode | No | `/think` + `/no_think` | Qwen3 |
| 4-bit size | 1.8 GB | 2.3 GB | Llama (smaller) |
| Context | 128K | 32K (→131K) | Llama (longer) |
| LoRA empathy fine-tuning | Works | Best-in-class results | Qwen3 |
| MLX availability | ✅ default | ✅ mlx-community | Tie |

Qwen3-4B's dual mode is uniquely suited to ADHD coaching:
- `/no_think` for quick emotional acknowledgments (sub-2s response, feels empathetic)
- `/think` for complex coaching ("help me break down this overwhelming project")

**Alternative choices (in order of preference):**
1. **Qwen3-4B** — recommended primary choice
2. **SmolLM3 3B** — if you want Apache 2.0 license and smaller footprint (2.0 GB)
3. **Gemma 3 4B-IT** — if you want Google ecosystem compatibility
4. **Qwen3-1.7B** — if memory is critically tight (use as daily driver, Qwen3-4B for venting)

### Load-on-Demand Architecture for 16GB M4

The LLM is NOT always resident. It loads when needed and unloads when idle.

**File: `backend/services/mlx_inference.py`** (COMPLETE REPLACEMENT)

```python
"""
On-device LLM inference using Apple MLX framework.
Load-on-demand architecture for 16GB M4 Mac.

Primary: Qwen3-4B Instruct 4-bit (~2.3 GB) — loaded when coaching needed
Fallback: Qwen3-1.7B 4-bit (~1.1 GB) — lighter option if memory pressure detected

Install models:
  pip install mlx-lm
  # Models auto-download from HuggingFace on first use
"""

import gc
import time
from datetime import datetime
from typing import Optional
from config import settings

class MLXInference:
    """
    Manages on-device LLM lifecycle: load → generate → unload.

    Memory pattern:
    - Classifier (all-MiniLM-L6-v2, ~80MB) → always resident
    - Coaching LLM (Qwen3-4B, ~2.3GB) → load on demand, unload after TTL
    - SenticNet (Python API, ~50MB) → always resident

    Peak AI memory: ~2.5 GB. Leaves 3-5 GB headroom on 16GB M4.

    CRITICAL: MLX cannot run two models concurrently on separate threads
    (Metal thread-safety issue, GitHub #3078). The classifier uses
    sentence-transformers (CPU/MPS), not MLX, so there's no conflict.
    """

    # Model registry
    MODELS = {
        "primary": "mlx-community/Qwen3-4B-4bit",
        "light": "mlx-community/Qwen3-1.7B-4bit",
    }

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.current_model_key: Optional[str] = None
        self.last_used: Optional[datetime] = None
        self.adapter_path: Optional[str] = settings.MLX_ADAPTER_PATH

    def _load_model(self, model_key: str = "primary"):
        """Load model into memory. Takes ~2-5 seconds on M4 SSD."""
        if self.current_model_key == model_key:
            return  # Already loaded

        # Unload current model first
        self._unload()

        from mlx_lm import load
        model_id = self.MODELS[model_key]

        start = time.time()
        self.model, self.tokenizer = load(
            model_id,
            adapter_path=self.adapter_path if self.adapter_path else None
        )
        load_time = time.time() - start

        self.current_model_key = model_key
        self.last_used = datetime.now()

        # Log for FYP evaluation data
        print(f"[MLX] Loaded {model_id} in {load_time:.1f}s")

    def _unload(self):
        """Free model memory. Essential on 16GB machine."""
        if self.model is not None:
            self.model = None
            self.tokenizer = None
            self.current_model_key = None
            gc.collect()
            # MLX lazy evaluation means garbage collection frees GPU memory
            print("[MLX] Model unloaded, memory freed")

    def maybe_unload_if_idle(self):
        """
        Called periodically (e.g., every 30s from a background timer).
        Unloads model if not used for TTL seconds.
        """
        if self.model is None or self.last_used is None:
            return

        idle_seconds = (datetime.now() - self.last_used).total_seconds()
        if idle_seconds > settings.MLX_KEEP_ALIVE_SECONDS:
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

        The LLM receives pre-computed emotional context from SenticNet
        (the hard part — emotion detection) and just needs to generate
        a natural, empathetic response (the easy part for an LLM).

        Args:
            system_prompt: ADHD coaching persona + rules
            user_message: The user's venting/question text
            senticnet_context: Structured emotion data from SenticNet pipeline
            whoop_context: Recovery score, HRV, sleep quality
            adhd_profile_context: ASRS severity, subtype, medication status
            use_thinking: If True, use /think mode for complex reasoning
        """
        # Ensure model is loaded
        self._load_model("primary")
        self.last_used = datetime.now()

        # Build context sections
        context_parts = []

        if senticnet_context:
            context_parts.append(f"""<senticnet_analysis>
Primary emotion: {senticnet_context.get('primary_emotion', 'unknown')}
Hourglass state: introspection={senticnet_context.get('introspection', 0):.2f}, temper={senticnet_context.get('temper', 0):.2f}, attitude={senticnet_context.get('attitude', 0):.2f}, sensitivity={senticnet_context.get('sensitivity', 0):.2f}
Intensity: {senticnet_context.get('intensity_score', 0):.0f}/100
Engagement: {senticnet_context.get('engagement_score', 0):.0f}/100
Well-being: {senticnet_context.get('wellbeing_score', 0):.0f}/100
Safety level: {senticnet_context.get('safety_level', 'normal')}
Key concepts: {', '.join(senticnet_context.get('concepts', [])[:5])}
ADHD state: {senticnet_context.get('primary_adhd_state', 'neutral')}
</senticnet_analysis>""")

        if whoop_context:
            context_parts.append(f"""<whoop_data>
Recovery: {whoop_context.get('recovery_score', 'unknown')}% ({whoop_context.get('recovery_tier', 'unknown')})
HRV: {whoop_context.get('hrv_rmssd', 'unknown')}ms
Sleep performance: {whoop_context.get('sleep_performance', 'unknown')}%
</whoop_data>""")

        if adhd_profile_context:
            context_parts.append(f"""<adhd_profile>
Subtype: {adhd_profile_context.get('subtype', 'unspecified')}
Severity: {adhd_profile_context.get('severity', 'unknown')}
Medicated: {adhd_profile_context.get('is_medicated', False)}
</adhd_profile>""")

        context_section = "\n".join(context_parts)

        # Thinking mode prefix for Qwen3
        thinking_prefix = "/think\n" if use_thinking else "/no_think\n"

        # Build messages for chat template
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{context_section}"},
            {"role": "user", "content": f"{thinking_prefix}{user_message}"},
        ]

        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Generate
        from mlx_lm import generate
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
        """
        Generate a personalized ADHD morning briefing from Whoop data.
        Uses /no_think for fast, conversational output.
        """
        system_prompt = """You are a supportive ADHD coach delivering a morning briefing.
Rules:
- Under 5 sentences total
- Start with energy/mood acknowledgment based on recovery data
- Give ONE specific, actionable recommendation for today
- Use warm, encouraging tone (never clinical or robotic)
- If recovery is low, emphasize self-compassion over productivity"""

        whoop_summary = f"""Recovery: {whoop_data.get('recovery_score', '?')}% ({whoop_data.get('recovery_tier', '?')})
Sleep: {whoop_data.get('sleep_performance', '?')}%, {whoop_data.get('disturbance_count', '?')} disturbances
HRV: {whoop_data.get('hrv_rmssd', '?')}ms, RHR: {whoop_data.get('resting_hr', '?')}
Deep sleep: {whoop_data.get('sws_percentage', '?')}%, REM: {whoop_data.get('rem_percentage', '?')}%
Recommended focus blocks: {whoop_data.get('recommended_focus_block_minutes', 25)} minutes"""

        return self.generate_coaching_response(
            system_prompt=system_prompt,
            user_message=f"Generate my morning briefing based on this data:\n{whoop_summary}",
            adhd_profile_context=adhd_profile,
            use_thinking=False,  # Fast mode for morning briefing
            max_tokens=200,
            temperature=0.6,
        )


# Default ADHD coaching system prompt
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

### Updated Config

**In `backend/config.py`, REPLACE the LLM section:**
```python
# LLM — UPDATED for M4 16GB
MLX_PRIMARY_MODEL: str = "mlx-community/Qwen3-4B-4bit"
MLX_LIGHT_MODEL: str = "mlx-community/Qwen3-1.7B-4bit"
MLX_ADAPTER_PATH: str = "./adapters/adhd-coach"  # LoRA adapter (few MB)
MLX_KEEP_ALIVE_SECONDS: int = 120  # Unload LLM after 2 min idle
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # For classification Layer 4

# Cloud fallback (optional, for complex conversations)
ANTHROPIC_API_KEY: str = ""  # Claude API for deep coaching sessions
OPENAI_API_KEY: str = ""     # GPT-4o-mini for Mem0 embeddings
```

---

## 3. SENTICNET AS THE EMOTION ENGINE (NOT THE LLM)

This is the key architectural insight: **SenticNet does the emotion detection, the LLM just generates natural language.** Small LLMs are bad at detecting emotions but good at generating empathetic text when told what emotion to respond to.

### The Prompt Injection Pattern

```python
# In backend/services/chat_processor.py

async def process_vent_message(text: str, user_context: dict, conversation_id: str) -> dict:
    """
    Full pipeline: SenticNet detects emotion → LLM generates response.

    1. SenticNet does the HARD part (emotion detection, safety check)
    2. LLM does the EASY part (generate empathetic response given context)
    """
    # Step 1: SenticNet analysis (fast, deterministic, no LLM needed)
    senticnet_result = await senticnet_pipeline.full_analysis(text)

    # Step 2: Safety check FIRST (non-negotiable)
    if senticnet_result.safety_flags.is_critical:
        return {
            "response": "I hear you, and I want you to know that what you're feeling matters. "
                       "If things feel really heavy right now, these people are trained to help:",
            "resources": CRISIS_RESOURCES_SG,
            "senticnet": senticnet_result.dict(),
            "used_llm": False,
        }

    # Step 3: Build structured context for LLM
    senticnet_context = {
        "primary_emotion": senticnet_result.emotion_profile.primary_emotion,
        "introspection": senticnet_result.emotion_profile.hourglass_dimensions.get("introspection", 0),
        "temper": senticnet_result.emotion_profile.hourglass_dimensions.get("temper", 0),
        "attitude": senticnet_result.emotion_profile.hourglass_dimensions.get("attitude", 0),
        "sensitivity": senticnet_result.emotion_profile.hourglass_dimensions.get("sensitivity", 0),
        "intensity_score": senticnet_result.adhd_signals.intensity_score,
        "engagement_score": senticnet_result.adhd_signals.engagement_score,
        "wellbeing_score": senticnet_result.adhd_signals.wellbeing_score,
        "safety_level": senticnet_result.safety_flags.level,
        "concepts": [c for c in senticnet_result.concepts.get("concepts", [])[:5]],
        "primary_adhd_state": senticnet_result.adhd_signals.primary_adhd_state if hasattr(senticnet_result.adhd_signals, 'primary_adhd_state') else "neutral",
    }

    # Step 4: Determine if /think or /no_think mode
    # Use /think for complex situations, /no_think for quick acknowledgments
    use_thinking = (
        abs(senticnet_result.adhd_signals.intensity_score) > 60  # High emotional intensity
        or "help" in text.lower()  # Explicit request for help
        or len(text) > 200  # Long message = complex situation
    )

    # Step 5: Generate response with LLM (loads on demand if needed)
    response = mlx_inference.generate_coaching_response(
        system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
        user_message=text,
        senticnet_context=senticnet_context,
        use_thinking=use_thinking,
    )

    # Step 6: Store in memory for pattern tracking
    await memory_service.add_conversation_memory(
        messages=[
            {"role": "user", "content": text},
            {"role": "assistant", "content": response},
        ],
        metadata={
            "senticnet": senticnet_context,
            "used_thinking": use_thinking,
        }
    )

    return {
        "response": response,
        "senticnet": senticnet_context,
        "used_llm": True,
        "thinking_mode": "think" if use_thinking else "no_think",
    }
```

---

## 4. LoRA FINE-TUNING RECIPE (DEVELOPER ONLY, NOT PER-USER)

Fine-tuning happens ONCE during development. The adapter ships with the app. Users never fine-tune anything.

### One-Time Setup (Run on Your M4 MacBook, Close Other Apps First)

```bash
# Step 1: Install MLX fine-tuning tools
pip install mlx-lm

# Step 2: Prepare training data (JSONL format)
# Each line: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
# Sources:
#   - EmpatheticDialogues (25K conversations, 32 emotions)
#   - ESConv (1,300 strategy-annotated emotional support conversations)
#   - Custom ADHD scenarios (you generate these — see below)

# Step 3: Fine-tune Qwen3-4B with QLoRA
# Close browser and IDE first — this needs ~8-10 GB
mlx_lm.lora \
    --model mlx-community/Qwen3-4B-4bit \
    --train \
    --data ./training_data \
    --adapter-path ./adapters/adhd-coach \
    --iters 1000 \
    --batch-size 2 \
    --lora-rank 16 \
    --lora-alpha 32 \
    --num-layers 8
# Takes ~15-30 minutes on M4
# Produces a ~5-10 MB adapter file

# Step 4: Test the adapter
mlx_lm.generate \
    --model mlx-community/Qwen3-4B-4bit \
    --adapter-path ./adapters/adhd-coach \
    --prompt "I can't focus on anything today and I feel like a failure"

# Step 5: Optionally fuse adapter into base model for faster loading
mlx_lm.fuse \
    --model mlx-community/Qwen3-4B-4bit \
    --adapter-path ./adapters/adhd-coach \
    --save-path ./models/qwen3-4b-adhd-coach
```

### Custom ADHD Training Data Generation

Generate synthetic ADHD coaching dialogues using Claude API:

```python
# scripts/generate_adhd_training_data.py

ADHD_SCENARIOS = [
    "I've been staring at this blank document for 2 hours and I can't start writing",
    "My boss just criticized my work and I want to quit everything",
    "I hyperfocused on reorganizing my desk instead of doing my assignment",
    "Everyone in the meeting seemed to understand except me",
    "I forgot to take my medication and now my whole day is ruined",
    "I'm switching between 10 tabs and can't settle on anything",
    "I feel like I'm faking being functional and everyone will find out",
    "My partner is frustrated because I forgot our plans again",
    "I have 5 deadlines this week and I can't prioritize any of them",
    "I just scrolled social media for 3 hours when I meant to work",
    # ... generate 200+ scenarios covering RSD, task paralysis,
    # emotional dysregulation, time blindness, working memory issues
]

# Use Claude API to generate ideal coaching responses for each scenario
# Then format as JSONL for MLX fine-tuning
```

### Training Data Checklist

| Dataset | Size | Source | Use |
|---------|------|--------|-----|
| EmpatheticDialogues | 25K conversations | HuggingFace | General empathy training |
| ESConv | 1,300 conversations | HuggingFace | Strategy-annotated support |
| Custom ADHD scenarios | 200-500 pairs | You generate via Claude | ADHD-specific patterns |
| **Total** | **~27K examples** | | |

---

## 5. MEMORY BUDGET SUMMARY FOR M4 16GB

```
┌──────────────────────────────────────────────────────┐
│              16 GB UNIFIED MEMORY                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  macOS + system services:           ~5 GB  (fixed)   │
│  User apps (browser, IDE, etc):     ~4-6 GB (varies) │
│  ─────────────────────────────────────────────────── │
│  Available for AI stack:            ~5-7 GB           │
│                                                      │
│  ALWAYS RESIDENT:                                    │
│  ├── Python FastAPI backend:         ~100 MB          │
│  ├── SenticNet Python API:           ~50 MB           │
│  ├── all-MiniLM-L6-v2 (classifier): ~80 MB           │
│  ├── PostgreSQL:                     ~100 MB          │
│  └── Subtotal:                       ~330 MB          │
│                                                      │
│  ON-DEMAND (loads when needed, unloads after 2 min): │
│  ├── Qwen3-4B 4-bit:                ~2.3 GB          │
│  └── Peak total:                     ~2.6 GB          │
│                                                      │
│  HEADROOM remaining:                 ~2.4-4.4 GB     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 6. DEPENDENCIES UPDATE

### Replace in `backend/requirements.txt`:

```
# REMOVE these lines:
# mlx-lm==0.21.*        # OLD — was for Llama 3.2 3B

# ADD/UPDATE these lines:
mlx-lm>=0.31.0          # Qwen3-4B support, LoRA, prompt caching
sentence-transformers>=3.0.0  # all-MiniLM-L6-v2 for classification
numpy>=1.26.0           # For embedding similarity computation
```

### Model Download Script

**Add to `scripts/setup.sh`:**
```bash
# Download classification model (tiny, ~80MB)
echo "Downloading classification model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Download coaching LLM (first use downloads ~2.3GB)
echo "Downloading Qwen3-4B coaching model..."
python -c "from mlx_lm import load; m, t = load('mlx-community/Qwen3-4B-4bit'); del m, t"

# Optional: Download lighter model for memory-constrained situations
echo "Downloading Qwen3-1.7B light model..."
python -c "from mlx_lm import load; m, t = load('mlx-community/Qwen3-1.7B-4bit'); del m, t"
```

---

## 7. BACKGROUND UNLOADER

**Add to `backend/main.py` lifespan:**
```python
import asyncio

async def model_cleanup_task():
    """Periodically check if LLM should be unloaded to free memory."""
    while True:
        mlx_inference.maybe_unload_if_idle()
        await asyncio.sleep(30)  # Check every 30 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_memory()

    # Start background model cleanup
    cleanup_task = asyncio.create_task(model_cleanup_task())

    yield

    cleanup_task.cancel()
```

---

## HOW THIS FILE RELATES TO THE OTHER DOCUMENTS

```
adhd-second-brain-blueprint.md     → Core architecture, all services, database, API contracts
architecture-diagram.mermaid       → Visual component diagram
adhd-second-brain-supplement.md    → HCI design, onboarding, JITAI updates, notification tiers
adhd-second-brain-models.md        → THIS FILE: AI model choices, inference code, fine-tuning
(this document)

PRIORITY ORDER (if conflicts exist):
1. This file (models.md) overrides blueprint Section 7 and config.py LLM settings
2. Supplement overrides blueprint where noted
3. Blueprint is the base for everything else
```

**For Claude Code**: Read all four files. Use `blueprint.md` for overall architecture, `supplement.md` for HCI/ADHD design, and `models.md` (this file) for all AI model decisions, inference implementations, and classification code.

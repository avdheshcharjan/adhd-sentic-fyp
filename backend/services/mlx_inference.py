"""
On-device LLM inference using Apple MLX framework.
Load-on-demand architecture for 16GB M4 Mac.

Primary: Qwen3-4B Instruct 4-bit (~2.3 GB) — loaded when coaching needed
Fallback: Qwen3-1.7B 4-bit (~1.1 GB) — lighter option if memory pressure detected
"""

import gc
import logging
import re
import time
from datetime import datetime
from typing import Optional

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

        from mlx_lm import load
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
                f"Polarity: {senticnet_context.get('polarity_score', 0):.0f}/100\n"
                f"Intensity: {senticnet_context.get('intensity_score', 0):.0f}/100\n"
                f"Engagement: {senticnet_context.get('engagement_score', 0):.0f}/100\n"
                f"Well-being: {senticnet_context.get('wellbeing_score', 0):.0f}/100\n"
                f"Hourglass dimensions (joy↔sadness, calm↔anger, pleasant↔disgust, eager↔fear):\n"
                f"  Introspection: {senticnet_context.get('introspection', 0):.1f}\n"
                f"  Temper: {senticnet_context.get('temper', 0):.1f}\n"
                f"  Attitude: {senticnet_context.get('attitude', 0):.1f}\n"
                f"  Sensitivity: {senticnet_context.get('sensitivity', 0):.1f}\n"
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

        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        sampler = make_sampler(temp=temperature)
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        )

        # Strip Qwen3 thinking tags — model emits them even with /no_think prefix
        response = re.sub(r"<think>.*?</think>\s*", "", response, flags=re.DOTALL)
        return response.strip()

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

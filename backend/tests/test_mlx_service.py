"""
Phase 1 — Task 1.2: MLX LLM Service Smoke Tests (Real Integration).

Tests the on-device Qwen3-4B via MLX. This is the most critical component.
Requires the model to be downloaded: mlx-community/Qwen3-4B-4bit

Run with: pytest tests/test_mlx_service.py -v --timeout=300 -s
"""

import asyncio
import gc
import random
import time

import psutil
import pytest

random.seed(42)


def _get_rss_mb() -> float:
    """Get current process RSS in MB."""
    return psutil.Process().memory_info().rss / (1024 * 1024)


class TestModelLoading:
    """Test 1: Model loading."""

    def test_model_loads_successfully(self):
        from services.mlx_inference import MLXInference

        inference = MLXInference()
        rss_before = _get_rss_mb()

        start = time.perf_counter()
        inference._load_model("primary")
        load_time = time.perf_counter() - start

        rss_after = _get_rss_mb()

        assert inference.model is not None, "Model failed to load"
        assert inference.tokenizer is not None, "Tokenizer failed to load"
        assert inference.current_model_key == "primary"

        print(f"\n  Model load time: {load_time:.1f}s")
        print(f"  RSS before: {rss_before:.0f} MB")
        print(f"  RSS after:  {rss_after:.0f} MB")
        print(f"  RSS delta:  {rss_after - rss_before:.0f} MB")

        # Memory should increase after loading (model is ~2.3GB)
        assert rss_after > rss_before, "Memory did not increase after loading model"

        # Clean up
        inference._unload()


class TestBasicGeneration:
    """Test 2: Basic generation."""

    def test_basic_generation(self):
        from services.mlx_inference import MLXInference

        inference = MLXInference()

        start = time.perf_counter()
        response = inference.generate_coaching_response(
            system_prompt="You are a helpful assistant.",
            user_message="Hello, how are you?",
            max_tokens=100,
            use_thinking=False,
        )
        total_time = time.perf_counter() - start

        assert response, "Response is empty"
        assert isinstance(response, str)
        assert len(response) > 5, f"Response too short: {response!r}"

        # Basic coherence: should contain common English words
        response_lower = response.lower()
        has_english = any(
            word in response_lower
            for word in ["i", "the", "a", "is", "am", "you", "hello", "hi", "how", "help"]
        )
        assert has_english, f"Response doesn't look like coherent English: {response!r}"

        # Estimate tokens (rough: ~4 chars/token)
        tokens = len(response) // 4

        print(f"\n  Response: {response[:200]}")
        print(f"  Total generation time: {total_time:.2f}s")
        print(f"  Estimated tokens: {tokens}")

        # Clean up
        inference._unload()


class TestCoachingGeneration:
    """Test 3: Coaching-style generation."""

    def test_adhd_coaching_response(self):
        from services.mlx_inference import MLXInference
        from services.constants import ADHD_COACHING_SYSTEM_PROMPT

        inference = MLXInference()
        response = inference.generate_coaching_response(
            system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
            user_message="I can't focus on my work today, I keep getting distracted",
            max_tokens=250,
            use_thinking=False,
        )

        assert response, "Coaching response is empty"

        # Basic relevance: response should reference focus/distraction/strategies
        response_lower = response.lower()
        relevance_keywords = [
            "focus", "distract", "try", "break", "task", "time",
            "start", "help", "feel", "hear", "understand", "tough",
            "hard", "mind", "attention", "step", "small",
        ]
        has_relevant_content = any(kw in response_lower for kw in relevance_keywords)
        assert has_relevant_content, f"Response doesn't seem relevant to ADHD coaching: {response!r}"

        # Response length: 50-500 tokens (~200-2000 chars)
        token_estimate = len(response) // 4
        assert token_estimate >= 10, f"Response too short ({token_estimate} tokens): {response!r}"
        assert token_estimate <= 500, f"Response too long ({token_estimate} tokens)"

        # No harmful/crisis content
        harmful_keywords = ["kill", "suicide", "die", "self-harm", "end your life"]
        for kw in harmful_keywords:
            assert kw not in response_lower, f"Response contains harmful content: '{kw}'"

        print(f"\n  Coaching response: {response[:300]}")

        inference._unload()


class TestThinkingModeToggle:
    """Test 4: Thinking mode toggle (Qwen3 feature)."""

    def test_think_vs_no_think(self):
        from services.mlx_inference import MLXInference
        from services.constants import ADHD_COACHING_SYSTEM_PROMPT

        inference = MLXInference()
        prompt = "I feel overwhelmed by my todo list and don't know where to start"

        # /no_think mode
        start = time.perf_counter()
        no_think_response = inference.generate_coaching_response(
            system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=250,
            use_thinking=False,
        )
        no_think_time = time.perf_counter() - start

        # /think mode
        start = time.perf_counter()
        think_response = inference.generate_coaching_response(
            system_prompt=ADHD_COACHING_SYSTEM_PROMPT,
            user_message=prompt,
            max_tokens=400,
            use_thinking=True,
        )
        think_time = time.perf_counter() - start

        assert no_think_response, "/no_think response is empty"
        assert think_response, "/think response is empty"

        print(f"\n  /no_think time: {no_think_time:.2f}s | len: {len(no_think_response)} chars")
        print(f"  /think time:    {think_time:.2f}s | len: {len(think_response)} chars")
        print(f"  /no_think response: {no_think_response[:200]}")
        print(f"  /think response:    {think_response[:200]}")

        # Both should be valid text
        assert len(no_think_response) > 10
        assert len(think_response) > 10

        inference._unload()


class TestAutoUnload:
    """Test 5: Auto-unload behavior."""

    def test_unload_frees_memory(self):
        from services.mlx_inference import MLXInference

        inference = MLXInference()
        rss_pre_load = _get_rss_mb()

        # Load model
        inference._load_model("primary")
        assert inference.model is not None

        # Generate one response to exercise the model
        inference.generate_coaching_response(
            system_prompt="You are helpful.",
            user_message="Hi",
            max_tokens=20,
            use_thinking=False,
        )
        rss_loaded = _get_rss_mb()

        # Unload
        inference._unload()
        gc.collect()
        rss_unloaded = _get_rss_mb()

        print(f"\n  RSS pre-load:  {rss_pre_load:.0f} MB")
        print(f"  RSS loaded:    {rss_loaded:.0f} MB")
        print(f"  RSS unloaded:  {rss_unloaded:.0f} MB")
        print(f"  Memory freed:  {rss_loaded - rss_unloaded:.0f} MB")

        assert inference.model is None
        assert inference.tokenizer is None
        assert inference.current_model_key is None

        # Memory should drop after unload (may not be exact due to Python GC)
        # At least some memory should be freed
        assert rss_unloaded < rss_loaded, "Memory did not decrease after unload"


class TestSequentialRequests:
    """Test 6: Sequential multiple requests (MLX is not thread-safe)."""

    def test_sequential_generation(self):
        """Multiple sequential requests should all complete without errors."""
        from services.mlx_inference import MLXInference

        inference = MLXInference()

        prompts = [
            "I can't focus today",
            "I'm feeling overwhelmed",
            "Help me get started on my work",
        ]
        results = []

        start = time.perf_counter()
        for prompt in prompts:
            response = inference.generate_coaching_response(
                system_prompt="You are a coach.",
                user_message=prompt,
                max_tokens=50,
                use_thinking=False,
            )
            results.append(response)
        total_time = time.perf_counter() - start

        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        for i, r in enumerate(results):
            assert r, f"Response {i} is empty"
            assert isinstance(r, str)
            print(f"\n  Response {i}: {r[:100]}")

        print(f"\n  Total sequential time: {total_time:.2f}s")
        print(f"  Avg per request: {total_time / 3:.2f}s")

        inference._unload()

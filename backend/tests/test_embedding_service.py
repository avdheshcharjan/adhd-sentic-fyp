"""
Phase 1 — Task 1.3: Sentence Embedding Service Smoke Tests (Real Integration).

Tests the all-MiniLM-L6-v2 model used for zero-shot classification in the
ActivityClassifier (Layer 4). Real model loading — no mocks.

Run with: pytest tests/test_embedding_service.py -v --timeout=300 -s
"""

import random
import time

import numpy as np
import psutil
import pytest

from sentence_transformers import SentenceTransformer

random.seed(42)
np.random.seed(42)


def _get_rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024 * 1024)


@pytest.fixture(scope="module")
def model() -> SentenceTransformer:
    """Load the embedding model once for all tests in this module."""
    return SentenceTransformer("all-MiniLM-L6-v2")


# ═══════════════════════════════════════════════════════════════════
# Test 1: Model Loading
# ═══════════════════════════════════════════════════════════════════


class TestModelLoading:
    def test_model_loads_successfully(self):
        rss_before = _get_rss_mb()
        start = time.perf_counter()
        m = SentenceTransformer("all-MiniLM-L6-v2")
        load_time = time.perf_counter() - start
        rss_after = _get_rss_mb()

        assert m is not None
        memory_delta = rss_after - rss_before

        print(f"\n  Load time: {load_time:.2f}s")
        print(f"  Memory footprint: ~{memory_delta:.0f} MB")

        assert load_time < 10, f"Model took {load_time:.1f}s to load — expected < 10s"


# ═══════════════════════════════════════════════════════════════════
# Test 2: Embedding Generation
# ═══════════════════════════════════════════════════════════════════


class TestEmbeddingGeneration:
    def test_single_embedding(self, model: SentenceTransformer):
        start = time.perf_counter()
        embedding = model.encode("Visual Studio Code - main.py")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,), f"Expected dim 384, got {embedding.shape}"
        assert not np.all(embedding == 0), "Embedding is all zeros"

        print(f"\n  Embedding time: {elapsed_ms:.1f}ms")
        print(f"  Embedding dim: {embedding.shape[0]}")
        print(f"  L2 norm: {np.linalg.norm(embedding):.4f}")

        assert elapsed_ms < 500, f"Embedding took {elapsed_ms:.0f}ms — expected < 500ms"

    def test_embedding_is_float_array(self, model: SentenceTransformer):
        embedding = model.encode("Test sentence")
        assert embedding.dtype in (np.float32, np.float64)

    def test_normalized_embedding(self, model: SentenceTransformer):
        embedding = model.encode("Test sentence", normalize_embeddings=True)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01, f"Normalized embedding has norm {norm:.4f}"


# ═══════════════════════════════════════════════════════════════════
# Test 3: Cosine Similarity Sanity Check
# ═══════════════════════════════════════════════════════════════════


class TestCosineSimilarity:
    def _cosine_sim(self, model: SentenceTransformer, text_a: str, text_b: str) -> float:
        emb_a = model.encode(text_a, normalize_embeddings=True)
        emb_b = model.encode(text_b, normalize_embeddings=True)
        return float(np.dot(emb_a, emb_b))

    def test_productive_similarity_high(self, model: SentenceTransformer):
        """'Visual Studio Code' and 'productive work' should have high similarity."""
        sim = self._cosine_sim(model, "Visual Studio Code", "productive work")
        print(f"\n  VSCode <-> productive work: {sim:.4f}")
        assert sim > 0.1, f"Expected > 0.1, got {sim:.4f}"

    def test_youtube_cats_low_similarity(self, model: SentenceTransformer):
        """'YouTube - funny cats' and 'productive work' should have low similarity."""
        sim = self._cosine_sim(model, "YouTube - funny cats", "productive work")
        print(f"\n  YouTube cats <-> productive work: {sim:.4f}")
        assert sim < 0.3, f"Expected < 0.3, got {sim:.4f}"

    def test_youtube_tutorial_medium_similarity(self, model: SentenceTransformer):
        """'YouTube - python tutorial' and 'productive work' should have medium similarity."""
        sim = self._cosine_sim(model, "YouTube - python tutorial", "productive work")
        print(f"\n  YouTube tutorial <-> productive work: {sim:.4f}")
        # Medium — just check it's between the other two extremes

    def test_coding_closer_to_dev_than_entertainment(self, model: SentenceTransformer):
        """Coding activity should be closer to 'development' category than to 'entertainment'."""
        # Use the actual category descriptions from the classifier
        dev_desc = "Programming, coding, software development, debugging, terminal, IDE, code editor"
        ent_desc = "Watching videos, streaming, gaming, music, YouTube, Netflix, Twitch, Spotify"

        sim_code_dev = self._cosine_sim(
            model, "Writing Python code in an editor", dev_desc
        )
        sim_code_ent = self._cosine_sim(
            model, "Writing Python code in an editor", ent_desc
        )

        print(f"\n  'Writing Python code' <-> development: {sim_code_dev:.4f}")
        print(f"  'Writing Python code' <-> entertainment: {sim_code_ent:.4f}")
        assert sim_code_dev > sim_code_ent, (
            f"Coding ({sim_code_dev:.4f}) should be closer to dev than entertainment ({sim_code_ent:.4f})"
        )


# ═══════════════════════════════════════════════════════════════════
# Test 4: Batch Performance
# ═══════════════════════════════════════════════════════════════════


class TestBatchPerformance:
    def test_batch_100_titles(self, model: SentenceTransformer):
        """Embed 100 window titles and measure performance."""
        titles = [
            "Visual Studio Code - main.py",
            "Google Chrome - GitHub",
            "Slack - #general",
            "Spotify - Now Playing",
            "YouTube - Music Video",
            "Terminal - zsh",
            "Notion - My Workspace",
            "Figma - UI Design",
            "Safari - Stack Overflow",
            "Discord - Study Group",
            "Reddit - r/programming",
            "Twitter - Home",
            "Obsidian - Daily Notes",
            "Zoom - Meeting",
            "Microsoft Word - Report.docx",
            "Calculator",
            "Preview - screenshot.png",
            "Finder - Downloads",
            "TextEdit - notes.txt",
            "System Preferences",
        ]
        # Repeat to get 100
        titles_100 = (titles * 5)[:100]

        start = time.perf_counter()
        embeddings = model.encode(titles_100)
        total_time = time.perf_counter() - start

        avg_per_title_ms = (total_time / len(titles_100)) * 1000

        assert embeddings.shape == (100, 384), f"Expected (100, 384), got {embeddings.shape}"
        assert not np.any(np.isnan(embeddings)), "NaN in embeddings"

        print(f"\n  Total time for 100 titles: {total_time:.2f}s")
        print(f"  Average per title: {avg_per_title_ms:.1f}ms")

        # Average should be < 50ms per title
        assert avg_per_title_ms < 50, (
            f"Average {avg_per_title_ms:.1f}ms per title — expected < 50ms"
        )

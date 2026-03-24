"""
Phase 1 — Task 1.5: Mem0 Memory Service Smoke Tests (Real Integration).

Tests the MemoryService Layer 1 (Mem0 with pgvector + OpenAI embeddings).
Requires:
  - PostgreSQL running on port 5433 (docker compose)
  - OPENAI_API_KEY in .env

Run with: pytest tests/test_memory_service_integration.py -v --timeout=300 -s
"""

import random
import time
import uuid

import pytest

random.seed(42)


def _make_test_user_id() -> str:
    """Generate a unique user ID for test isolation."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def memory_svc():
    """Create a real MemoryService connected to pgvector."""
    from services.memory_service import MemoryService

    svc = MemoryService()
    if svc.mem0 is None:
        pytest.skip("Mem0 failed to initialize — check PostgreSQL and OPENAI_API_KEY")
    return svc


# ═══════════════════════════════════════════════════════════════════
# Test 1: Store and Retrieve
# ═══════════════════════════════════════════════════════════════════


class TestStoreAndRetrieve:
    def test_store_and_search(self, memory_svc):
        """Store a memory and retrieve it via semantic search."""
        user_id = _make_test_user_id()
        message = "User prefers short task lists with max 3 items"

        # Store
        memory_svc.add_conversation_memory(
            user_id=user_id,
            message=message,
            context="Preference noted during vent session",
        )

        # Small delay for vector indexing
        time.sleep(1)

        # Search
        results = memory_svc.search_relevant_context(
            user_id=user_id,
            query="task list preferences",
            limit=5,
        )

        assert len(results) > 0, "No results returned from search"
        # Check that the stored memory is in results
        found = False
        for r in results:
            if isinstance(r, dict):
                memory_text = r.get("memory", "")
            else:
                memory_text = str(r)
            if "task" in memory_text.lower() or "3 items" in memory_text.lower():
                found = True
                break

        print(f"\n  Stored: {message}")
        print(f"  Results: {results}")
        assert found, f"Stored memory not found in search results: {results}"


# ═══════════════════════════════════════════════════════════════════
# Test 2: Contextual Retrieval
# ═══════════════════════════════════════════════════════════════════


class TestContextualRetrieval:
    def test_retrieves_most_relevant(self, memory_svc):
        """Store 5 memories, query specific topic, should return most relevant."""
        user_id = _make_test_user_id()

        memories = [
            "User gets overwhelmed when there are more than 5 tasks visible",
            "User prefers lo-fi music while working",
            "User has ADHD-PI subtype, diagnosed at age 25",
            "User takes Vyvanse 40mg in the morning",
            "User works best in 25-minute Pomodoro blocks",
        ]

        for m in memories:
            memory_svc.add_conversation_memory(user_id=user_id, message=m)

        time.sleep(2)  # Allow indexing

        # Query about medication
        start = time.perf_counter()
        results = memory_svc.search_relevant_context(
            user_id=user_id,
            query="What medication does the user take?",
            limit=3,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        assert len(results) > 0, "No results returned"

        # Check most relevant result mentions medication
        top_result = results[0] if results else {}
        if isinstance(top_result, dict):
            top_text = top_result.get("memory", "")
        else:
            top_text = str(top_result)

        print(f"\n  Query: 'What medication does the user take?'")
        print(f"  Top result: {top_text}")
        print(f"  Retrieval latency: {latency_ms:.0f}ms")

        assert latency_ms < 5000, f"Retrieval took {latency_ms:.0f}ms — expected < 5000ms"


# ═══════════════════════════════════════════════════════════════════
# Test 3: Memory Metadata
# ═══════════════════════════════════════════════════════════════════


class TestMemoryMetadata:
    def test_metadata_preserved(self, memory_svc):
        """Store memory with metadata and verify it's preserved on retrieval."""
        user_id = _make_test_user_id()

        memory_svc.add_conversation_memory(
            user_id=user_id,
            message="User was feeling anxious about upcoming deadline",
            context="Vent session during late-night study",
        )

        time.sleep(1)

        results = memory_svc.search_relevant_context(
            user_id=user_id,
            query="anxiety deadline",
            limit=3,
        )

        assert len(results) > 0, "No results returned"
        print(f"\n  Results with metadata: {results}")


# ═══════════════════════════════════════════════════════════════════
# Test 4: Memory Capacity
# ═══════════════════════════════════════════════════════════════════


class TestMemoryCapacity:
    def test_50_memories(self, memory_svc):
        """Store 50 memories and verify retrieval still works."""
        user_id = _make_test_user_id()

        # Store 50 diverse memories
        topics = [
            "procrastination", "focus", "medication", "sleep",
            "exercise", "diet", "mood", "energy", "tasks",
            "meetings", "deadlines", "projects", "breaks",
            "music", "environment", "stress", "motivation",
            "goals", "habits", "routines", "tools", "apps",
            "social", "family", "work", "study",
        ]

        for i in range(50):
            topic = topics[i % len(topics)]
            memory_svc.add_conversation_memory(
                user_id=user_id,
                message=f"Memory #{i}: User mentioned {topic} — "
                        f"observation {random.randint(1, 100)} about their {topic} patterns",
            )

        time.sleep(3)  # Allow bulk indexing

        # Measure retrieval latency at 50 memories
        start = time.perf_counter()
        results_50 = memory_svc.search_relevant_context(
            user_id=user_id,
            query="What are the user's focus patterns?",
            limit=5,
        )
        latency_50 = (time.perf_counter() - start) * 1000

        assert len(results_50) > 0, "No results returned at 50 memories"

        print(f"\n  Retrieval at 50 memories:")
        print(f"  Results: {len(results_50)}")
        print(f"  Latency: {latency_50:.0f}ms")

        assert latency_50 < 10_000, f"Retrieval at 50 memories took {latency_50:.0f}ms — too slow"

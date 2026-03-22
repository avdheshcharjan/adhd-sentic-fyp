"""
Brain Dump Reminder Queue — tracks captured brain dumps pending reminder delivery.

When a brain dump is captured, it's added to the queue. The JITAI engine checks
this queue and fires a reminder intervention when the user is idle/unfocused.
Once delivered, the reminder is removed from the queue.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("adhd-brain.brain-dump-reminder")


@dataclass
class PendingReminder:
    entry_id: str
    content_preview: str  # truncated to ~80 chars
    captured_at: datetime
    delivered: bool = False


class BrainDumpReminderQueue:
    """In-memory queue of brain dumps awaiting reminder delivery."""

    def __init__(self) -> None:
        self._pending: list[PendingReminder] = []

    def add(self, entry_id: str, content: str) -> None:
        preview = content[:80].rstrip() + ("..." if len(content) > 80 else "")
        reminder = PendingReminder(
            entry_id=entry_id,
            content_preview=preview,
            captured_at=datetime.now(timezone.utc),
        )
        self._pending.append(reminder)
        logger.info(f"Brain dump reminder queued: {entry_id}")

    def pop_next(self) -> PendingReminder | None:
        """Pop the oldest undelivered reminder, or None if empty."""
        for i, r in enumerate(self._pending):
            if not r.delivered:
                self._pending.pop(i)
                return r
        return None

    def has_pending(self) -> bool:
        return any(not r.delivered for r in self._pending)

    def time_since_oldest(self) -> float:
        """Minutes since the oldest pending reminder was captured."""
        for r in self._pending:
            if not r.delivered:
                elapsed = (datetime.now(timezone.utc) - r.captured_at).total_seconds() / 60
                return elapsed
        return 0.0

    def clear(self) -> None:
        self._pending.clear()

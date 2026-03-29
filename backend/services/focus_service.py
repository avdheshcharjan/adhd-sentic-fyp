"""
Focus service — manages task creation, focus sessions, and task lifecycle.

Uses SQLAlchemy async sessions for persistence (FocusTask model).
In-memory focus timer state (elapsed tracking) lives here since it's
process-local and doesn't need to survive restarts.
"""

import time
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal
from db.models import FocusTask


class FocusService:
    def __init__(self):
        # In-memory timer state
        self._current_task_id: Optional[str] = None
        self._focus_total: float = 25 * 60  # seconds
        self._focus_label: str = "Focus"
        self._is_running: bool = False
        self._last_start_time: Optional[float] = None
        self._accumulated_time: float = 0.0

    # ── Task Creation ──────────────────────────────────────────────

    async def create_task(self, name: str, duration_seconds: int) -> Dict[str, Any]:
        """Create a new task in the DB and start a focus session."""
        task_id = str(uuid.uuid4())

        async with AsyncSessionLocal() as db:
            task = FocusTask(
                id=task_id,
                name=name,
                duration_seconds=duration_seconds,
                progress=0.0,
                is_active=True,
            )
            db.add(task)
            await db.commit()

        # Start focus session for this task
        self._current_task_id = task_id
        self._task_name = name
        self._focus_total = float(duration_seconds)
        self._focus_label = "Focus"
        self._accumulated_time = 0.0
        self._last_start_time = time.time()
        self._is_running = True

        return {
            "id": task_id,
            "name": name,
            "progress": 0.0,
            "is_active": True,
        }

    # ── Queries ────────────────────────────────────────────────────

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        if self._current_task_id is None:
            return None
        # Return in-memory view (DB is source of truth but we avoid async here)
        return {
            "id": self._current_task_id,
            "name": self._task_name or "Task",
            "progress": self._compute_progress(),
            "is_active": self._is_running,
        }

    def get_focus_session(self) -> Optional[Dict[str, Any]]:
        elapsed = self._accumulated_time
        if self._is_running and self._last_start_time is not None:
            elapsed += (time.time() - self._last_start_time)

        return {
            "elapsed": float(elapsed),
            "total": float(self._focus_total),
            "is_running": bool(self._is_running),
            "label": str(self._focus_label),
        }

    # ── Actions ────────────────────────────────────────────────────

    def toggle_focus(self) -> Dict[str, str]:
        if self._is_running:
            # Pause
            if self._last_start_time:
                self._accumulated_time += (time.time() - self._last_start_time)
            self._last_start_time = None
            self._is_running = False
            return {"status": "paused"}
        else:
            # Resume
            self._last_start_time = time.time()
            self._is_running = True
            return {"status": "started"}

    async def complete_task(self, task_id: str) -> Dict[str, str]:
        if self._current_task_id != task_id:
            return {"status": "not_found", "id": task_id}

        # Stop the timer
        if self._is_running:
            self.toggle_focus()

        # Persist completion to DB
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(FocusTask)
                .where(FocusTask.id == task_id)
                .values(progress=1.0, is_active=False)
            )
            await db.commit()

        self._current_task_id = None
        self._task_name = None
        return {"status": "completed", "id": task_id}

    # ── Private ────────────────────────────────────────────────────

    _task_name: Optional[str] = None

    def _compute_progress(self) -> float:
        if self._focus_total <= 0:
            return 0.0
        elapsed = self._accumulated_time
        if self._is_running and self._last_start_time is not None:
            elapsed += (time.time() - self._last_start_time)
        return min(elapsed / self._focus_total, 1.0)

    async def _load_task_from_db(self, task_id: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(FocusTask).where(FocusTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return None
            return {
                "id": str(task.id),
                "name": task.name,
                "progress": task.progress,
                "is_active": task.is_active,
            }

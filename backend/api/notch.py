"""
Notch/Swift App endpoints (Phase 4 / Notch Island integration)
Handles the /api/v1/ prefix routes requested by the Swift desktop widget.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from services.google_calendar import google_calendar_service

logger = logging.getLogger("adhd-brain.notch")

router = APIRouter(prefix="/api/v1", tags=["notch"])

class CaptureRequest(BaseModel):
    text: str
    source: str = "notch_quick_capture"

@router.get("/tasks/current")
async def get_current_task():
    # Placeholder returning the exact format expected by TaskItem.swift
    return {
        "id": "task-1",
        "name": "Write Chapter 3",
        "progress": 0.75,
        "is_active": True
    }

@router.get("/focus/session")
async def get_focus_session():
    # Placeholder returning the exact format expected by FocusSession.swift
    return {
        "elapsed": 120.0,
        "total": 1500.0,
        "is_running": True,
        "label": "Focus"
    }

@router.get("/calendar/upcoming")
async def get_upcoming_events(limit: int = 3):
    """Fetch upcoming events from Google Calendar. Falls back to empty list if not authenticated."""
    if not google_calendar_service.is_authenticated:
        logger.warning("Google Calendar not authenticated — returning empty events")
        return []

    try:
        events = await google_calendar_service.get_upcoming_events(max_results=limit)
        return events
    except Exception as e:
        logger.error(f"Failed to fetch Google Calendar events: {e}")
        return []

@router.get("/emotion/current")
async def get_current_emotion():
    # Needs to match EmotionState in Swift which expects a simple JSON string value natively
    return "focused"

@router.get("/interventions/pending")
async def get_pending_intervention():
    # Return None if no intervention, else format of InterventionMessage
    return None

@router.get("/progress/today")
async def get_daily_progress():
    # Format of DailyProgress
    return {
        "tasks_completed": 3,
        "focus_sessions": 2,
        "total_focus_minutes": 50
    }

@router.post("/capture")
async def capture_thought(req: CaptureRequest):
    return {"status": "captured", "text": req.text}

@router.post("/interventions/{id}/acknowledge")
async def acknowledge_intervention(id: str):
    return {"status": "acknowledged", "id": id}

@router.post("/focus/toggle")
async def toggle_focus():
    return {"status": "toggled"}

@router.post("/tasks/{id}/complete")
async def complete_task(id: str):
    return {"status": "completed", "id": id}

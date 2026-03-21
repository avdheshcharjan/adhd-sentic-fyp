"""
Notch/Swift App endpoints (Phase 4 / Notch Island integration)
Handles the /api/v1/ prefix routes requested by the Swift desktop widget.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from services.google_calendar import google_calendar_service
from services.shared_state import focus_service, metrics_engine
from services.insights_service import InsightsService

logger = logging.getLogger("adhd-brain.notch")

router = APIRouter(prefix="/api/v1", tags=["notch"])

_insights = InsightsService()

class CaptureRequest(BaseModel):
    text: str
    source: str = "notch_quick_capture"

@router.get("/tasks/current")
async def get_current_task():
    return focus_service.get_current_task()

@router.get("/focus/session")
async def get_focus_session():
    return focus_service.get_focus_session()

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
    """Return current behavioral state from live metrics. Matches EmotionState enum in Swift."""
    metrics = metrics_engine.get_metrics()
    return metrics.behavioral_state

@router.get("/interventions/pending")
async def get_pending_intervention():
    # Return None if no intervention, else format of InterventionMessage
    return None

@router.get("/progress/today")
async def get_daily_progress():
    """Aggregate today's progress from InsightsService. Matches DailyProgress struct in Swift."""
    daily = await _insights.get_daily()
    return {
        "tasks_completed": daily.interventions_accepted,
        "focus_sessions": daily.interventions_triggered,
        "total_focus_minutes": int(daily.total_focus_minutes),
    }

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Aggregate today's stats from InsightsService. Matches DashboardStats struct in Swift."""
    daily = await _insights.get_daily()
    timeline_raw = await _insights._get_timeline()
    emotions = await _insights._get_recent_emotions()

    # Build timeline segments as fractional durations (Swift expects 0-1 fractions)
    total_duration = sum(b["duration_sec"] for b in timeline_raw) if timeline_raw else 1
    focus_timeline = [
        {
            "id": str(uuid.uuid4())[:8],
            "category": block["state"],
            "duration": round(block["duration_sec"] / total_duration, 3),
        }
        for block in timeline_raw
    ]

    # Average recent emotion profiles into PASE scores
    pleasantness = 0.0
    attention = 0.0
    sensitivity = 0.0
    aptitude = 0.0
    if emotions:
        for e in emotions:
            profile = e.get("emotion_profile", {})
            pleasantness += profile.get("pleasantness", 0.0)
            attention += profile.get("attention", 0.0)
            sensitivity += profile.get("sensitivity", 0.0)
            aptitude += profile.get("aptitude", 0.0)
        n = len(emotions)
        pleasantness /= n
        attention /= n
        sensitivity /= n
        aptitude /= n

    return {
        "total_focus_minutes": int(daily.total_focus_minutes),
        "total_active_minutes": int(daily.total_active_minutes),
        "interventions_triggered": daily.interventions_triggered,
        "interventions_accepted": daily.interventions_accepted,
        "focus_timeline": focus_timeline,
        "emotion_scores": {
            "pleasantness": round(pleasantness, 2),
            "attention": round(attention, 2),
            "sensitivity": round(sensitivity, 2),
            "aptitude": round(aptitude, 2),
        },
    }

@router.get("/dashboard/weekly")
async def get_dashboard_weekly():
    """Aggregate weekly report from InsightsService. Matches WeeklyReport struct in Swift."""
    weekly = await _insights.get_weekly()
    today_str = date.today().isoformat()

    # Map daily_focus_scores [{date, focus_pct, distraction_pct}] → DayReport shape
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    days = []
    for i, d in enumerate(weekly.daily_focus_scores):
        d_date = date.fromisoformat(d["date"])
        days.append({
            "id": f"d{i}",
            "day": DAY_NAMES[d_date.weekday()],
            "focus_ratio": round(d["focus_pct"] / 100.0, 3),
            "distraction_ratio": round(d["distraction_pct"] / 100.0, 3),
            "is_today": d["date"] == today_str,
        })

    # best_day / worst_day — InsightsService returns ISO date strings, Swift expects day name
    best_day = "--"
    if weekly.best_focus_day:
        best_day = DAY_NAMES[date.fromisoformat(weekly.best_focus_day).weekday()]
    worst_day = "--"
    if weekly.worst_focus_day:
        worst_day = DAY_NAMES[date.fromisoformat(weekly.worst_focus_day).weekday()]

    return {
        "days": days,
        "avg_focus": round(weekly.avg_focus_percentage / 100.0, 3),
        "avg_distraction": round(weekly.avg_distraction_percentage / 100.0, 3),
        "total_interventions": weekly.total_interventions,
        "acceptance_rate": round(weekly.intervention_acceptance_rate / 100.0, 3),
        "best_day": best_day,
        "worst_day": worst_day,
        "trend": weekly.trend,
    }

@router.post("/capture")
async def capture_thought(req: CaptureRequest):
    return {"status": "captured", "text": req.text}

@router.post("/interventions/{id}/acknowledge")
async def acknowledge_intervention(id: str):
    return {"status": "acknowledged", "id": id}

@router.post("/focus/toggle")
async def toggle_focus():
    return focus_service.toggle_focus()

@router.post("/tasks/{id}/complete")
async def complete_task(id: str):
    return focus_service.complete_task(id)

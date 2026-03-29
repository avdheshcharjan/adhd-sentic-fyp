"""
Notch/Swift App endpoints (Phase 4 / Notch Island integration)
Handles the /api/v1/ prefix routes requested by the Swift desktop widget.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.google_calendar import google_calendar_service
import services.shared_state as shared_state
from services.shared_state import focus_service, metrics_engine
from services.insights_service import InsightsService
from services.setfit_service import blend_pase
from services.snapshot_service import SnapshotService

logger = logging.getLogger("adhd-brain.notch")

router = APIRouter(prefix="/api/v1", tags=["notch"])

_insights = InsightsService()
_snapshots = SnapshotService()

class CaptureRequest(BaseModel):
    text: str
    source: str = "notch_quick_capture"

class CreateTaskRequest(BaseModel):
    name: str
    duration_seconds: int
    start_focus: bool = True

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

@router.get("/focus/off-task")
async def get_off_task_status():
    """Return whether the user is currently off-task."""
    return {"off_task": shared_state.is_off_task}

@router.get("/emotion/current")
async def get_current_emotion():
    """Return current behavioral state from live metrics. Matches EmotionState enum in Swift."""
    metrics = metrics_engine.get_metrics()
    return metrics.behavioral_state

@router.get("/interventions/pending")
async def get_pending_intervention():
    """Return the latest pending intervention from JITAI, mapped to InterventionMessage shape for Swift."""
    intervention = shared_state.pending_intervention
    if intervention is None:
        return None
    # Map Intervention model → InterventionMessage shape expected by Swift
    action_label = "Got it"
    if intervention.actions:
        action_label = intervention.actions[0].label
    return {
        "id": intervention.id,
        "title": intervention.acknowledgment,
        "body": intervention.suggestion,
        "emoji": intervention.actions[0].emoji if intervention.actions else "\u26A1",
        "action_label": action_label,
        "notification_tier": intervention.notification_tier,
    }

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

    # Compute PASE scores from SetFit labels stored in emotion_profile.
    # Each SenticAnalysis row has primary_emotion (SetFit label) and setfit_confidence.
    # We map label → canonical PASE profile, blend with confidence, then average.
    pase_accum: dict[str, float] = {"pleasantness": 0.0, "attention": 0.0, "sensitivity": 0.0, "aptitude": 0.0}
    pase_count = 0
    for e in emotions:
        profile = e.get("emotion_profile", {})
        label = profile.get("primary_emotion", "")
        confidence = profile.get("setfit_confidence", 0.5)
        if not label or label == "unknown":
            continue
        blended = blend_pase(label, confidence)
        for k in pase_accum:
            pase_accum[k] += blended[k]
        pase_count += 1

    if pase_count > 0:
        for k in pase_accum:
            pase_accum[k] = round(pase_accum[k] / pase_count, 2)

    return {
        "total_focus_minutes": int(daily.total_focus_minutes),
        "total_active_minutes": int(daily.total_active_minutes),
        "interventions_triggered": daily.interventions_triggered,
        "interventions_accepted": daily.interventions_accepted,
        "focus_timeline": focus_timeline,
        "emotion_scores": pase_accum,
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

@router.post("/tasks/create")
async def create_task(req: CreateTaskRequest):
    """Create a new task and optionally start a focus session."""
    task = await focus_service.create_task(
        name=req.name,
        duration_seconds=req.duration_seconds,
    )
    return task

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
    return await focus_service.complete_task(id)


# ── History / Snapshots ────────────────────────────────────────────

@router.get("/dashboard/history")
async def list_history(start: str, end: str):
    """List snapshot summaries for a date range. Both start and end are YYYY-MM-DD, inclusive."""
    return await _snapshots.list_snapshots(start, end)


@router.get("/dashboard/history/{date_str}")
async def get_history_detail(date_str: str):
    """Fetch full snapshot for a specific date."""
    try:
        return await _snapshots.get_snapshot(date_str)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/dashboard/snapshot")
async def trigger_snapshot(date_str: Optional[str] = None):
    """Manually trigger snapshot save. Defaults to today."""
    return await _snapshots.save_daily_snapshot(date_str)

"""Insights endpoints — stubs for Phase 1, enriched in later phases."""

from fastapi import APIRouter

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/current")
async def get_current_state():
    """Current ADHD state + metrics snapshot (stub)."""
    return {
        "metrics": {},
        "behavioral_state": "unknown",
        "pending_intervention": None,
        "current_session": None,
    }


@router.get("/daily")
async def get_daily_summary():
    """Today's summary (stub)."""
    return {"message": "Daily summary not yet implemented."}


@router.get("/weekly")
async def get_weekly_review():
    """Weekly pattern review (stub)."""
    return {"message": "Weekly review not yet implemented."}

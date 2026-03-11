"""Insights endpoints — live metrics, daily summary, weekly trends."""

from typing import Optional

from fastapi import APIRouter, Query

from models.insights import CurrentInsights, DailyInsights, WeeklyInsights
from services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["insights"])

_service = InsightsService()


@router.get("/current", response_model=CurrentInsights)
async def get_current_state():
    """Current ADHD state + metrics snapshot from in-memory engine."""
    return _service.get_current()


@router.get("/daily", response_model=DailyInsights)
async def get_daily_summary(
    date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
):
    """Today's aggregated activity summary (or specific date)."""
    return await _service.get_daily(date_str=date)


@router.get("/weekly", response_model=WeeklyInsights)
async def get_weekly_review(
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD (default: today)"),
):
    """7-day pattern review ending on the given date (default: today)."""
    return await _service.get_weekly(end_date_str=end_date)

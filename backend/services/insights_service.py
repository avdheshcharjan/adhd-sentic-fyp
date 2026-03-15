"""
Insights aggregation service.

- get_current(): live metrics from in-memory engine
- get_daily(): query DB for today's activity aggregates
- get_weekly(): query DB for 7-day trends
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, and_

from db.database import AsyncSessionLocal
from db.models import ActivityLog, InterventionHistory
from models.insights import (
    AppUsageSummary,
    CurrentInsights,
    DailyInsights,
    DashboardData,
    WeeklyInsights,
)
from db.models import SenticAnalysis
from services.shared_state import metrics_engine

logger = logging.getLogger("adhd-brain.insights")

# Categories
PRODUCTIVE_CATEGORIES = {
    "development", "writing", "research", "productivity", "design",
}
DISTRACTING_CATEGORIES = {
    "social_media", "entertainment", "news", "shopping",
}

# Each activity entry represents ~2 seconds
SECONDS_PER_ENTRY = 2


class InsightsService:
    """Aggregates ADHD behavioral data for insights endpoints."""

    def get_current(self) -> CurrentInsights:
        """Return live in-memory metrics snapshot."""
        metrics = metrics_engine.get_metrics()
        return CurrentInsights(
            metrics=metrics.model_dump(),
            behavioral_state=metrics.behavioral_state,
            current_app=metrics.current_app,
            current_category=metrics.current_category,
            pending_intervention=None,
        )

    async def get_daily(self, date_str: str | None = None) -> DailyInsights:
        """Query DB for a single day's aggregated activity."""
        target_date = (
            date.fromisoformat(date_str) if date_str else date.today()
        )
        start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        async with AsyncSessionLocal() as session:
            # Fetch activities
            result = await session.execute(
                select(ActivityLog).where(
                    and_(
                        ActivityLog.timestamp >= start,
                        ActivityLog.timestamp < end,
                    )
                )
            )
            activities = result.scalars().all()

            # Fetch interventions
            intv_result = await session.execute(
                select(InterventionHistory).where(
                    and_(
                        InterventionHistory.timestamp >= start,
                        InterventionHistory.timestamp < end,
                    )
                )
            )
            interventions = intv_result.scalars().all()

        return self._aggregate_daily(activities, interventions, target_date)

    async def get_weekly(self, end_date_str: str | None = None) -> WeeklyInsights:
        """Query DB for 7-day trend analysis."""
        end_d = (
            date.fromisoformat(end_date_str) if end_date_str else date.today()
        )
        start_d = end_d - timedelta(days=6)

        daily_summaries = []
        for i in range(7):
            d = start_d + timedelta(days=i)
            summary = await self.get_daily(d.isoformat())
            daily_summaries.append(summary)

        return self._aggregate_weekly(daily_summaries, start_d, end_d)

    async def get_dashboard(self) -> DashboardData:
        """Combine all data sources into a single dashboard payload."""
        current = self.get_current()
        daily = await self.get_daily()
        weekly = await self.get_weekly()

        # Whoop morning briefing (best-effort)
        whoop_data = None
        try:
            from services.whoop_service import WhoopService
            whoop = WhoopService()
            briefing = await whoop.generate_morning_briefing()
            whoop_data = briefing.model_dump()
        except Exception:
            pass

        # Recent emotion analyses (last 24h)
        emotions = await self._get_recent_emotions()

        # Today's activity timeline
        timeline = await self._get_timeline()

        return DashboardData(
            current=current,
            daily=daily,
            weekly=weekly,
            whoop=whoop_data,
            emotions=emotions,
            timeline=timeline,
        )

    async def _get_recent_emotions(self) -> list[dict]:
        """Fetch last 24h of SenticNet emotion analyses."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SenticAnalysis)
                .where(SenticAnalysis.timestamp >= cutoff)
                .order_by(SenticAnalysis.timestamp.desc())
                .limit(50)
            )
            rows = result.scalars().all()
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "emotion_profile": r.emotion_profile,
            }
            for r in rows
        ]

    async def _get_timeline(self) -> list[dict]:
        """Build today's activity timeline for the FocusTimeline component."""
        today = date.today()
        start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ActivityLog)
                .where(
                    and_(
                        ActivityLog.timestamp >= start,
                        ActivityLog.timestamp < end,
                    )
                )
                .order_by(ActivityLog.timestamp)
            )
            activities = result.scalars().all()

        if not activities:
            return []

        # Group consecutive same-category activities into blocks
        blocks: list[dict] = []
        current_block = None
        for a in activities:
            cat = a.category
            if a.is_idle:
                state = "idle"
            elif cat in PRODUCTIVE_CATEGORIES:
                state = "focused"
            elif cat in DISTRACTING_CATEGORIES:
                state = "distracted"
            else:
                state = "neutral"

            if current_block and current_block["state"] == state and current_block["app"] == a.app_name:
                current_block["end"] = a.timestamp.isoformat()
                current_block["duration_sec"] += SECONDS_PER_ENTRY
            else:
                current_block = {
                    "start": a.timestamp.isoformat(),
                    "end": a.timestamp.isoformat(),
                    "app": a.app_name,
                    "category": cat,
                    "state": state,
                    "duration_sec": SECONDS_PER_ENTRY,
                }
                blocks.append(current_block)
        return blocks

    # ── Private helpers ─────────────────────────────────────────────

    def _aggregate_daily(
        self,
        activities: list,
        interventions: list,
        target_date: date,
    ) -> DailyInsights:
        if not activities:
            return DailyInsights(date=target_date.isoformat())

        non_idle = [a for a in activities if not a.is_idle]
        active_minutes = len(non_idle) * SECONDS_PER_ENTRY / 60.0

        focus_entries = [
            a for a in non_idle if a.category in PRODUCTIVE_CATEGORIES
        ]
        distract_entries = [
            a for a in non_idle if a.category in DISTRACTING_CATEGORIES
        ]
        focus_min = len(focus_entries) * SECONDS_PER_ENTRY / 60.0
        distract_min = len(distract_entries) * SECONDS_PER_ENTRY / 60.0

        # Top apps by time
        app_counts: dict[str, dict] = {}
        for a in non_idle:
            key = a.app_name
            if key not in app_counts:
                app_counts[key] = {"count": 0, "category": a.category}
            app_counts[key]["count"] += 1

        top_apps = sorted(app_counts.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        top_app_summaries = [
            AppUsageSummary(
                app_name=name,
                category=data["category"],
                minutes=round(data["count"] * SECONDS_PER_ENTRY / 60.0, 1),
                percentage=round(data["count"] / len(non_idle) * 100, 1) if non_idle else 0,
            )
            for name, data in top_apps
        ]

        # Behavioral state distribution
        state_counts: dict[str, int] = {}
        for a in activities:
            m = a.metrics or {}
            state = m.get("behavioral_state", "unknown")
            state_counts[state] = state_counts.get(state, 0) + 1
        state_minutes = {
            s: round(c * SECONDS_PER_ENTRY / 60.0, 1)
            for s, c in state_counts.items()
        }

        # Context switches (count app transitions)
        switches = 0
        prev_app = None
        for a in sorted(activities, key=lambda x: x.timestamp):
            if prev_app and a.app_name != prev_app:
                switches += 1
            prev_app = a.app_name

        # Interventions
        accepted = sum(
            1 for i in interventions
            if i.user_response and i.user_response == "accepted"
        )

        return DailyInsights(
            date=target_date.isoformat(),
            total_active_minutes=round(active_minutes, 1),
            total_focus_minutes=round(focus_min, 1),
            total_distraction_minutes=round(distract_min, 1),
            focus_percentage=round(focus_min / active_minutes * 100, 1) if active_minutes > 0 else 0,
            distraction_percentage=round(distract_min / active_minutes * 100, 1) if active_minutes > 0 else 0,
            context_switches=switches,
            top_apps=top_app_summaries,
            interventions_triggered=len(interventions),
            interventions_accepted=accepted,
            behavioral_states=state_minutes,
        )

    def _aggregate_weekly(
        self,
        daily_summaries: list[DailyInsights],
        start_d: date,
        end_d: date,
    ) -> WeeklyInsights:
        daily_scores = [
            {
                "date": d.date,
                "focus_pct": d.focus_percentage,
                "distraction_pct": d.distraction_percentage,
            }
            for d in daily_summaries
        ]

        active_days = [d for d in daily_summaries if d.total_active_minutes > 0]
        avg_focus = (
            sum(d.focus_percentage for d in active_days) / len(active_days)
            if active_days else 0
        )
        avg_distraction = (
            sum(d.distraction_percentage for d in active_days) / len(active_days)
            if active_days else 0
        )

        total_intv = sum(d.interventions_triggered for d in daily_summaries)
        total_accepted = sum(d.interventions_accepted for d in daily_summaries)
        acceptance_rate = total_accepted / total_intv * 100 if total_intv > 0 else 0

        # Best/worst focus day
        best = max(active_days, key=lambda d: d.focus_percentage) if active_days else None
        worst = min(active_days, key=lambda d: d.focus_percentage) if active_days else None

        # Top apps across the week
        app_totals: dict[str, dict] = {}
        total_minutes = sum(d.total_active_minutes for d in daily_summaries)
        for d in daily_summaries:
            for app in d.top_apps:
                if app.app_name not in app_totals:
                    app_totals[app.app_name] = {"minutes": 0, "category": app.category}
                app_totals[app.app_name]["minutes"] += app.minutes
        weekly_apps = sorted(app_totals.items(), key=lambda x: x[1]["minutes"], reverse=True)[:5]
        weekly_app_summaries = [
            AppUsageSummary(
                app_name=name,
                category=data["category"],
                minutes=round(data["minutes"], 1),
                percentage=round(data["minutes"] / total_minutes * 100, 1) if total_minutes > 0 else 0,
            )
            for name, data in weekly_apps
        ]

        # Trend: compare first half vs second half focus
        trend = "stable"
        if len(active_days) >= 4:
            mid = len(active_days) // 2
            first_half = sum(d.focus_percentage for d in active_days[:mid]) / mid
            second_half = sum(d.focus_percentage for d in active_days[mid:]) / (len(active_days) - mid)
            diff = second_half - first_half
            if diff > 10:
                trend = "improving"
            elif diff < -10:
                trend = "declining"

        return WeeklyInsights(
            start_date=start_d.isoformat(),
            end_date=end_d.isoformat(),
            daily_focus_scores=daily_scores,
            avg_focus_percentage=round(avg_focus, 1),
            avg_distraction_percentage=round(avg_distraction, 1),
            total_interventions=total_intv,
            intervention_acceptance_rate=round(acceptance_rate, 1),
            best_focus_day=best.date if best else None,
            worst_focus_day=worst.date if worst else None,
            top_apps_weekly=weekly_app_summaries,
            trend=trend,
        )

"""
Daily snapshot service — saves and retrieves pre-computed daily dashboard summaries.

- save_daily_snapshot(): aggregate today's data and upsert into daily_snapshots table
- get_snapshot(): fetch a single date's snapshot
- list_snapshots(): fetch snapshot summaries for a date range
"""

import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select, and_

from db.database import AsyncSessionLocal
from db.models import DailySnapshot, WhoopLog
from services.insights_service import InsightsService
from services.setfit_service import blend_pase

logger = logging.getLogger("adhd-brain.snapshot")


class SnapshotService:
    """Manages daily snapshot persistence."""

    def __init__(self) -> None:
        self._insights = InsightsService()

    async def save_daily_snapshot(self, date_str: str | None = None) -> dict:
        """Aggregate a day's data and upsert into daily_snapshots.

        Args:
            date_str: YYYY-MM-DD string. Defaults to today.

        Returns:
            The snapshot data as a dict.
        """
        target_date = date_str or date.today().isoformat()
        logger.info(f"Saving daily snapshot for {target_date}")

        # Get daily insights (focus, distraction, apps, interventions, etc.)
        daily = await self._insights.get_daily(target_date)

        # Get timeline for the target date
        timeline_raw = await self._insights._get_timeline(target_date)

        # Build timeline segments as fractional durations
        total_duration = sum(b["duration_sec"] for b in timeline_raw) if timeline_raw else 1
        focus_timeline = [
            {
                "id": str(uuid.uuid4())[:8],
                "category": block["state"],
                "duration": round(block["duration_sec"] / total_duration, 3),
            }
            for block in timeline_raw
        ]

        # Compute PASE emotion scores for the target date
        emotions = await self._insights._get_recent_emotions(target_date)
        pase_accum: dict[str, float] = {
            "pleasantness": 0.0, "attention": 0.0,
            "sensitivity": 0.0, "aptitude": 0.0,
        }
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

        emotion_scores = None
        if pase_count > 0:
            emotion_scores = {
                k: round(v / pase_count, 2) for k, v in pase_accum.items()
            }

        # Fetch Whoop data for this date
        whoop_data = None
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WhoopLog).where(WhoopLog.date == target_date)
            )
            whoop_row = result.scalar_one_or_none()
            if whoop_row:
                whoop_data = {
                    "recovery_score": whoop_row.recovery_score,
                    "sleep_score": whoop_row.sleep_score,
                    "strain_score": whoop_row.strain_score,
                    "metrics": whoop_row.metrics,
                }

        # Serialize top_apps to dicts
        top_apps_list = [
            {
                "app_name": a.app_name,
                "category": a.category,
                "minutes": a.minutes,
                "percentage": a.percentage,
            }
            for a in daily.top_apps
        ]

        # Upsert snapshot
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DailySnapshot).where(DailySnapshot.date == target_date)
            )
            snapshot = result.scalar_one_or_none()

            if snapshot is None:
                snapshot = DailySnapshot(date=target_date)
                session.add(snapshot)

            snapshot.total_active_minutes = daily.total_active_minutes
            snapshot.total_focus_minutes = daily.total_focus_minutes
            snapshot.total_distraction_minutes = daily.total_distraction_minutes
            snapshot.focus_percentage = daily.focus_percentage
            snapshot.distraction_percentage = daily.distraction_percentage
            snapshot.context_switches = daily.context_switches
            snapshot.interventions_triggered = daily.interventions_triggered
            snapshot.interventions_accepted = daily.interventions_accepted
            snapshot.top_apps = top_apps_list
            snapshot.behavioral_states = daily.behavioral_states
            snapshot.focus_timeline = focus_timeline
            snapshot.emotion_scores = emotion_scores
            snapshot.whoop_recovery = whoop_data

            await session.commit()
            logger.info(f"Snapshot saved for {target_date}")

        return self._snapshot_to_dict(snapshot)

    async def get_snapshot(self, date_str: str) -> dict:
        """Fetch the full snapshot for a given date.

        Raises:
            ValueError: If no snapshot exists for the date.
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DailySnapshot).where(DailySnapshot.date == date_str)
            )
            snapshot = result.scalar_one_or_none()

        if snapshot is None:
            raise ValueError(f"No snapshot found for {date_str}")

        return self._snapshot_to_dict(snapshot)

    async def list_snapshots(self, start: str, end: str) -> list[dict]:
        """Return summary list of snapshots in a date range (inclusive)."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DailySnapshot)
                .where(
                    and_(
                        DailySnapshot.date >= start,
                        DailySnapshot.date <= end,
                    )
                )
                .order_by(DailySnapshot.date.desc())
            )
            snapshots = result.scalars().all()

        return [
            {
                "date": s.date,
                "focus_percentage": s.focus_percentage,
                "distraction_percentage": s.distraction_percentage,
                "total_active_minutes": s.total_active_minutes,
                "total_focus_minutes": s.total_focus_minutes,
            }
            for s in snapshots
        ]

    async def has_snapshot(self, date_str: str) -> bool:
        """Check if a snapshot exists for the given date."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DailySnapshot.id).where(DailySnapshot.date == date_str)
            )
            return result.scalar_one_or_none() is not None

    def _snapshot_to_dict(self, snapshot: DailySnapshot) -> dict:
        """Convert a DailySnapshot ORM object to a response dict."""
        return {
            "date": snapshot.date,
            "total_active_minutes": snapshot.total_active_minutes,
            "total_focus_minutes": snapshot.total_focus_minutes,
            "total_distraction_minutes": snapshot.total_distraction_minutes,
            "focus_percentage": snapshot.focus_percentage,
            "distraction_percentage": snapshot.distraction_percentage,
            "context_switches": snapshot.context_switches,
            "interventions_triggered": snapshot.interventions_triggered,
            "interventions_accepted": snapshot.interventions_accepted,
            "top_apps": snapshot.top_apps,
            "behavioral_states": snapshot.behavioral_states,
            "focus_timeline": snapshot.focus_timeline,
            "emotion_scores": snapshot.emotion_scores,
            "whoop_recovery": snapshot.whoop_recovery,
        }

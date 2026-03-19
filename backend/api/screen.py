"""
Screen activity endpoint — the hottest path in the system.
Called every ~2 seconds by the Swift menu bar app.
Target latency: <100ms.

Phase 4: Now wires JITAI engine for real-time intervention evaluation.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.repositories.pattern_repo import pattern_repo
from db.models import ActivityLog, SenticAnalysis
from services.senticnet_pipeline import SenticNetPipeline

from models.screen_activity import ScreenActivityInput, ScreenActivityResponse
from services.shared_state import classifier, metrics_engine, jitai_engine, xai_explainer

logger = logging.getLogger("adhd-brain.screen")

router = APIRouter(prefix="/screen", tags=["screen"])


@router.post("/activity", response_model=ScreenActivityResponse)
async def report_activity(activity: ScreenActivityInput, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Process a screen activity report from the Swift app.

    Pipeline:
      1. Classify activity (rule-based, <5ms)
      2. Update rolling metrics (in-memory, <1ms)
      3. Evaluate JITAI intervention need (<2ms)
      4. Generate XAI explanation if intervention triggered
      5. Return category + metrics + intervention (if any)
    """
    # Step 1: Classify
    category, layer = classifier.classify(
        app_name=activity.app_name,
        window_title=activity.window_title,
        url=activity.url,
    )

    # Step 2: Update metrics
    metrics = metrics_engine.update(
        app_name=activity.app_name,
        category=category,
        is_idle=activity.is_idle,
        timestamp=activity.timestamp,
    )

    # Enrich metrics with context fields for JITAI gates
    metrics.current_app = activity.app_name
    metrics.current_category = category

    # Step 3: Evaluate JITAI intervention need
    intervention = jitai_engine.evaluate(metrics)

    # Step 4: Attach XAI explanation if intervention triggered
    if intervention:
        explanation = xai_explainer.explain_intervention(
            intervention_type=intervention.type,
            metrics=metrics.model_dump(),
        )
        intervention.explanation = explanation.model_dump()

    # Step 5: Schedule background persistence + optional SenticNet enrichment
    background_tasks.add_task(persist_activity, db, activity, category, metrics.model_dump())

    # Schedule lightweight SenticNet (non-blocking); may be a no-op if disabled
    background_tasks.add_task(enrich_activity_with_senticnet, activity.window_title or activity.app_name, db)

    # Step 6: Return immediate response (keep latency low)
    return ScreenActivityResponse(
        category=category,
        metrics=metrics.model_dump(),
        intervention=intervention,
    )


async def persist_activity(db: AsyncSession, activity: ScreenActivityInput, category: str, metrics_snapshot: dict):
    """Persist ActivityLog row asynchronously."""
    try:
        obj = ActivityLog(
            app_name=activity.app_name,
            window_title=activity.window_title,
            url=activity.url,
            category=category,
            is_idle=activity.is_idle,
            timestamp=activity.timestamp,
            metrics=metrics_snapshot,
        )
        db.add(obj)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist activity: {e}")


async def enrich_activity_with_senticnet(text: str, db: AsyncSession):
    """Run lightweight SenticNet analysis on the window title and persist results.

    Runs SenticNetPipeline.lightweight and stores a SenticAnalysis row if available.
    """
    try:
        pipeline = SenticNetPipeline()
        result = await pipeline._run_lightweight(text)
        if result and getattr(result, "adhd_signals", None):
            sa = SenticAnalysis(
                text=text,
                source="screen_title",
                emotion_profile=(result.emotion.model_dump() if getattr(result, "emotion", None) else {}),
                safety_flags=(result.safety.model_dump() if getattr(result, "safety", None) else {}),
                adhd_signals=(result.adhd_signals.model_dump() if getattr(result, "adhd_signals", None) else {}),
            )
            db.add(sa)
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to enrich activity with SenticNet: {e}")

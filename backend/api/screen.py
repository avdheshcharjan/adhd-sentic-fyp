"""
Screen activity endpoint — the hottest path in the system.
Called every ~2 seconds by the Swift menu bar app.
Target latency: <100ms.
"""

from fastapi import APIRouter

from models.screen_activity import ScreenActivityInput, ScreenActivityResponse
from services.activity_classifier import ActivityClassifier
from services.adhd_metrics import ADHDMetricsEngine

router = APIRouter(prefix="/screen", tags=["screen"])

# ── Singleton instances (created once, shared across requests) ──────
_classifier = ActivityClassifier()
_metrics_engine = ADHDMetricsEngine()


@router.post("/activity", response_model=ScreenActivityResponse)
async def report_activity(activity: ScreenActivityInput):
    """
    Process a screen activity report from the Swift app.

    Pipeline:
      1. Classify activity (rule-based, <5ms)
      2. Update rolling metrics (in-memory, <1ms)
      3. Return category + metrics + intervention (if any)
    """
    # Step 1: Classify
    category, layer = _classifier.classify(
        app_name=activity.app_name,
        window_title=activity.window_title,
        url=activity.url,
    )

    # Step 2: Update metrics
    metrics = _metrics_engine.update(
        app_name=activity.app_name,
        category=category,
        is_idle=activity.is_idle,
        timestamp=activity.timestamp,
    )

    # Step 3: Build response (intervention = None for Phase 1,
    # JITAI engine added in Phase 4)
    return ScreenActivityResponse(
        category=category,
        metrics=metrics.model_dump(),
        intervention=None,
    )

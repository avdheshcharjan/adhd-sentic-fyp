"""
Screen activity endpoint — the hottest path in the system.
Called every ~2 seconds by the Swift menu bar app.
Target latency: <100ms.

Phase 4: Now wires JITAI engine for real-time intervention evaluation.
"""

from fastapi import APIRouter

from models.screen_activity import ScreenActivityInput, ScreenActivityResponse
from services.shared_state import classifier, metrics_engine, jitai_engine, xai_explainer

router = APIRouter(prefix="/screen", tags=["screen"])


@router.post("/activity", response_model=ScreenActivityResponse)
async def report_activity(activity: ScreenActivityInput):
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

    # Step 5: Build response
    return ScreenActivityResponse(
        category=category,
        metrics=metrics.model_dump(),
        intervention=intervention,
    )

# Phase 8: OpenClaw Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the ADHD Second Brain backend to Telegram and WhatsApp via OpenClaw custom skills, with fully implemented insights endpoints.

**Architecture:** Extract the in-memory metrics engine singleton into a shared module. Build insights service with DB queries for daily/weekly aggregates. Create 4 OpenClaw SKILL.md files that call backend REST endpoints. Configure HEARTBEAT.md for scheduled actions.

**Tech Stack:** Python/FastAPI (backend), SQLAlchemy async (DB queries), OpenClaw SKILL.md (Markdown skill definitions), Node.js 22+ (OpenClaw runtime)

---

### Task 1: Extract Metrics Engine to Shared State Module

**Files:**
- Create: `backend/services/shared_state.py`
- Modify: `backend/api/screen.py:19-23`

**Step 1: Create shared state module**

Create `backend/services/shared_state.py`:

```python
"""
Shared singleton instances — accessible from both screen.py and insights.py.

These are in-memory, process-level singletons. In production with multiple
workers, each worker gets its own copy (acceptable for this use case since
the Swift app sends to a single process).
"""

from services.activity_classifier import ActivityClassifier
from services.adhd_metrics import ADHDMetricsEngine
from services.jitai_engine import JITAIEngine
from services.xai_explainer import ConceptBottleneckExplainer

classifier = ActivityClassifier()
metrics_engine = ADHDMetricsEngine()
jitai_engine = JITAIEngine()
xai_explainer = ConceptBottleneckExplainer()
```

**Step 2: Update screen.py to use shared state**

Replace the 4 singleton lines in `backend/api/screen.py` (lines 19-23) with:

```python
from services.shared_state import classifier, metrics_engine, jitai_engine, xai_explainer
```

Update the route body to use new names:
- `_classifier` → `classifier`
- `_metrics_engine` → `metrics_engine`
- `_jitai_engine` → `jitai_engine`
- `_xai_explainer` → `xai_explainer`

**Step 3: Run existing tests to verify no regressions**

Run: `cd backend && python -m pytest tests/test_adhd_metrics.py tests/test_activity_classifier.py -v`
Expected: All tests PASS (no behavioral change)

**Step 4: Commit**

```bash
git add backend/services/shared_state.py backend/api/screen.py
git commit -m "refactor: extract singletons to shared_state module for insights access"
```

---

### Task 2: Create Insights Service with DB Queries

**Files:**
- Create: `backend/services/insights_service.py`
- Create: `backend/models/insights.py`
- Test: `backend/tests/test_insights_service.py`

**Step 1: Create insights response models**

Create `backend/models/insights.py`:

```python
"""Pydantic models for insights API responses."""

from pydantic import BaseModel


class CurrentInsights(BaseModel):
    """Live metrics snapshot + context."""

    metrics: dict
    behavioral_state: str = "unknown"
    current_app: str = ""
    current_category: str = ""
    pending_intervention: dict | None = None


class AppUsageSummary(BaseModel):
    """Usage stats for a single app."""

    app_name: str
    category: str
    minutes: float
    percentage: float


class DailyInsights(BaseModel):
    """Aggregated daily summary."""

    date: str
    total_active_minutes: float = 0.0
    total_focus_minutes: float = 0.0
    total_distraction_minutes: float = 0.0
    focus_percentage: float = 0.0
    distraction_percentage: float = 0.0
    context_switches: int = 0
    top_apps: list[AppUsageSummary] = []
    interventions_triggered: int = 0
    interventions_accepted: int = 0
    behavioral_states: dict = {}  # state -> minutes


class WeeklyInsights(BaseModel):
    """7-day pattern summary."""

    start_date: str
    end_date: str
    daily_focus_scores: list[dict] = []  # [{date, focus_pct, distraction_pct}]
    avg_focus_percentage: float = 0.0
    avg_distraction_percentage: float = 0.0
    total_interventions: int = 0
    intervention_acceptance_rate: float = 0.0
    best_focus_day: str | None = None
    worst_focus_day: str | None = None
    top_apps_weekly: list[AppUsageSummary] = []
    trend: str = "stable"  # "improving" | "declining" | "stable"
```

**Step 2: Write failing tests**

Create `backend/tests/test_insights_service.py`:

```python
"""Tests for the insights service — daily and weekly aggregations."""

from datetime import datetime, timezone, timedelta

import pytest

from services.insights_service import InsightsService


class TestCurrentInsights:
    def test_returns_live_metrics(self):
        service = InsightsService()
        result = service.get_current()
        assert "metrics" in result.model_dump()
        assert result.behavioral_state is not None

    def test_includes_behavioral_state(self):
        service = InsightsService()
        # Feed some data to the shared metrics engine first
        from services.shared_state import metrics_engine
        now = datetime.now()
        metrics_engine.update("VSCode", "development", False, now)
        result = service.get_current()
        assert result.behavioral_state != "unknown"


class TestDailyInsights:
    @pytest.mark.asyncio
    async def test_empty_day_returns_zeros(self):
        service = InsightsService()
        result = await service.get_daily(date_str="2020-01-01")
        assert result.total_active_minutes == 0.0
        assert result.total_focus_minutes == 0.0
        assert result.top_apps == []

    @pytest.mark.asyncio
    async def test_daily_date_format(self):
        service = InsightsService()
        result = await service.get_daily()
        assert len(result.date) == 10  # YYYY-MM-DD


class TestWeeklyInsights:
    @pytest.mark.asyncio
    async def test_weekly_has_7_days(self):
        service = InsightsService()
        result = await service.get_weekly()
        assert len(result.daily_focus_scores) <= 7

    @pytest.mark.asyncio
    async def test_weekly_trend_value(self):
        service = InsightsService()
        result = await service.get_weekly()
        assert result.trend in ("improving", "declining", "stable")
```

**Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_insights_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.insights_service'`

**Step 4: Implement insights service**

Create `backend/services/insights_service.py`:

```python
"""
Insights aggregation service.

- get_current(): live metrics from in-memory engine
- get_daily(): query DB for today's activity aggregates
- get_weekly(): query DB for 7-day trends
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, and_, cast, Date

from db.database import AsyncSessionLocal
from db.models import ActivityLog, InterventionHistory
from models.insights import (
    AppUsageSummary,
    CurrentInsights,
    DailyInsights,
    WeeklyInsights,
)
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

    # ── Private helpers ─────────────────────────────────────────────

    def _aggregate_daily(
        self,
        activities: list,
        interventions: list,
        target_date: date,
    ) -> DailyInsights:
        if not activities:
            return DailyInsights(date=target_date.isoformat())

        total = len(activities)
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
```

**Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_insights_service.py -v`
Expected: PASS for sync tests; async tests may need DB — they should pass with empty results.

**Step 6: Commit**

```bash
git add backend/models/insights.py backend/services/insights_service.py backend/tests/test_insights_service.py
git commit -m "feat(phase8): add insights service with daily/weekly aggregation"
```

---

### Task 3: Wire Insights Endpoints

**Files:**
- Modify: `backend/api/insights.py`

**Step 1: Replace stub endpoints with real implementation**

Replace entire `backend/api/insights.py` with:

```python
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
```

**Step 2: Verify server starts**

Run: `cd backend && python -c "from api.insights import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add backend/api/insights.py
git commit -m "feat(phase8): wire insights endpoints to InsightsService"
```

---

### Task 4: Create OpenClaw adhd-vent Skill

**Files:**
- Create: `openclaw-skills/adhd-vent/SKILL.md`

**Step 1: Create skill directory and file**

```bash
mkdir -p openclaw-skills/adhd-vent
```

Create `openclaw-skills/adhd-vent/SKILL.md`:

```markdown
---
name: adhd-vent
description: Empathetic ADHD coaching through emotional venting and regulation support
triggers:
  - emotional messages
  - venting
  - frustration
  - stress
  - overwhelm
  - any message that isn't a command
---

# ADHD Venting & Emotional Support

You are the conversational interface for an ADHD Second Brain system. When the user sends emotional or venting messages, process them through the backend's full SenticNet + LLM pipeline.

## How to Process Messages

For every user message:

1. Send the message to the backend:
   ```
   POST http://localhost:8420/chat/message
   Content-Type: application/json

   {
     "text": "<user's message>",
     "conversation_id": "<use the chat/thread ID>",
     "context": {"platform": "telegram"}
   }
   ```

2. Check the response's `used_llm` field:
   - If `true`: Reply with the `response` field. Show `suggested_actions` as quick-reply buttons if the platform supports them.
   - If `false`: This means a **CRITICAL safety situation** was detected. The `response` field contains a compassionate acknowledgement + crisis resources. Deliver it exactly as-is. Do NOT add your own commentary, coaching, or suggestions.

## Communication Rules (ADHD-Friendly)

- **Under 2–3 sentences.** ADHD working memory is limited. Never send walls of text.
- **Validate before suggesting.** "I hear that's frustrating" BEFORE "Have you tried..."
- **Maximum 2–3 choices** when offering options. Decision fatigue is real.
- **Upward framing.** "A 3-min reset helps 72% of the time" NOT "You've been distracted for an hour."
- **Never guilt, shame, or compare** to neurotypical standards.

## Critical Safety Handling

When `used_llm` is `false` in the response:
- The system detected depression + toxicity signals
- Do NOT attempt to be a therapist
- Acknowledge the user's pain
- Provide the crisis resources from the response
- Encourage professional support
- Do NOT add coaching, tips, or motivational content

## Error Handling

If the backend is unreachable (connection refused, timeout):
- Reply: "I'm having trouble connecting right now. If you need immediate support, please reach out to SOS CareText: 1-767-4357 or IMH Helpline: 6389-2222."
- Do NOT silently fail or give a generic error.
```

**Step 2: Commit**

```bash
git add openclaw-skills/adhd-vent/
git commit -m "feat(phase8): add adhd-vent OpenClaw skill"
```

---

### Task 5: Create OpenClaw morning-briefing Skill

**Files:**
- Create: `openclaw-skills/morning-briefing/SKILL.md`

**Step 1: Create skill directory and file**

```bash
mkdir -p openclaw-skills/morning-briefing
```

Create `openclaw-skills/morning-briefing/SKILL.md`:

```markdown
---
name: morning-briefing
description: Daily ADHD-optimized morning briefing from Whoop recovery data
triggers:
  - morning briefing
  - how did I sleep
  - morning report
  - recovery
---

# ADHD Morning Briefing

Delivers an ADHD-tailored morning briefing based on Whoop physiological data. Triggered automatically at 7:30 AM via HEARTBEAT, or on-demand when the user asks about their morning status.

## How to Fetch Data

```
GET http://localhost:8420/whoop/morning-briefing
```

The response contains:
- `recovery_score` (0-100)
- `recovery_tier` ("green" | "yellow" | "red")
- `recommended_focus_block_minutes` (15 | 25 | 45)
- `sleep_performance` (percentage)
- `sleep_notes` (list of observations)
- `hrv_rmssd`, `resting_hr`, `sws_percentage`, `rem_percentage`

## Message Templates

Format your reply based on the `recovery_tier`:

### 🟢 Green (recovery 67-100%)
"Good morning! Your body recovered well ({recovery_score}%). Great day for challenging work. Try {recommended_focus_block_minutes}-min focus blocks."

If there are sleep notes, add ONE relevant observation.

### 🟡 Yellow (recovery 34-66%)
"Morning! Moderate recovery ({recovery_score}%). Pace yourself — {recommended_focus_block_minutes}-min focus blocks with breaks."

If sleep performance is below 70%, mention it gently.

### 🔴 Red (recovery 0-33%)
"Hey, take it easy today. Recovery is low ({recovery_score}%). Stick to easy tasks, {recommended_focus_block_minutes}-min focus blocks."

Add a self-compassion note: "Low recovery happens. Being kind to yourself today IS productive."

## Rules

- Keep it to 2-3 sentences max
- Use the emoji tier indicator (🟢/🟡/🔴)
- Never guilt the user about poor sleep
- Frame recommendations positively

## Error Handling

If Whoop data is unavailable (503 or 401):
- Reply: "Couldn't fetch your Whoop data this morning. No worries — start with 25-min focus blocks and check in with yourself."
```

**Step 2: Commit**

```bash
git add openclaw-skills/morning-briefing/
git commit -m "feat(phase8): add morning-briefing OpenClaw skill"
```

---

### Task 6: Create OpenClaw focus-check Skill

**Files:**
- Create: `openclaw-skills/focus-check/SKILL.md`

**Step 1: Create skill directory and file**

```bash
mkdir -p openclaw-skills/focus-check
```

Create `openclaw-skills/focus-check/SKILL.md`:

```markdown
---
name: focus-check
description: On-demand ADHD focus status check with current metrics
triggers:
  - how am I doing
  - am I focused
  - focus check
  - what's my status
  - how's my focus
---

# Focus Status Check

Returns the user's current ADHD behavioral metrics on demand. Gives a quick, honest, non-judgmental snapshot of their focus state.

## How to Fetch Data

```
GET http://localhost:8420/insights/current
```

The response contains:
- `behavioral_state` ("focused" | "distracted" | "multitasking" | "hyperfocused" | "idle")
- `metrics.focus_score` (0-100%)
- `metrics.distraction_ratio` (0-1)
- `metrics.context_switch_rate_5min` (count)
- `metrics.current_streak_minutes` (minutes on current app)
- `metrics.hyperfocus_detected` (boolean)
- `current_app` (app name)
- `current_category` (category)

## Message Templates

### Focused
"You're doing great! {current_streak_minutes} min focused on {current_app}. Keep the flow going."

### Distracted
"Looks like things are a bit scattered — {context_switch_rate_5min} app switches in the last 5 min. Want to pick one thing to focus on for 10 minutes?"

### Multitasking
"You're bouncing between a few things. That's okay! Maybe pick the most important one and give it 15 minutes?"

### Hyperfocused
"You've been locked in on {current_app} for {current_streak_minutes} min — impressive! Just a gentle check: have you had water or stretched recently?"

### Idle
"Looks like you're on a break. When you're ready, try starting with the smallest next step."

## Rules

- One message, 1-2 sentences max
- Always validate before suggesting
- Never guilt about distraction
- If hyperfocused, gently remind about self-care without breaking flow
- Use upward framing always

## Error Handling

If backend is unreachable:
- Reply: "Can't check your metrics right now. If you're feeling scattered, try this: pick ONE task, set a 10-min timer, and just start."
```

**Step 2: Commit**

```bash
git add openclaw-skills/focus-check/
git commit -m "feat(phase8): add focus-check OpenClaw skill"
```

---

### Task 7: Create OpenClaw weekly-review Skill

**Files:**
- Create: `openclaw-skills/weekly-review/SKILL.md`

**Step 1: Create skill directory and file**

```bash
mkdir -p openclaw-skills/weekly-review
```

Create `openclaw-skills/weekly-review/SKILL.md`:

```markdown
---
name: weekly-review
description: Weekly ADHD pattern summary with focus trends and insights
triggers:
  - weekly review
  - how was my week
  - weekly summary
  - weekly patterns
---

# Weekly ADHD Pattern Review

Delivers a 7-day behavioral pattern summary. Triggered automatically on Sundays at 8 PM via HEARTBEAT, or on-demand.

## How to Fetch Data

```
GET http://localhost:8420/insights/weekly
```

The response contains:
- `avg_focus_percentage` (0-100)
- `avg_distraction_percentage` (0-100)
- `total_interventions` (count)
- `intervention_acceptance_rate` (0-100%)
- `best_focus_day` (date string)
- `worst_focus_day` (date string)
- `top_apps_weekly` (list of {app_name, minutes, percentage})
- `trend` ("improving" | "declining" | "stable")
- `daily_focus_scores` (list of {date, focus_pct, distraction_pct})

## Message Format

Structure the weekly review as a brief summary:

### Opening (based on trend)
- **Improving**: "Your week showed real progress! 📈"
- **Stable**: "Solid, consistent week. Here's the snapshot:"
- **Declining**: "This week was tough, and that's okay. Here's what happened:"

### Key Stats (pick 2-3 most relevant)
- "Average focus: {avg_focus_percentage}%"
- "Best day: {best_focus_day}" (only if notably better)
- "You used {interventions} interventions and found {acceptance_rate}% helpful"

### One Actionable Insight
Based on the data, offer ONE specific, actionable observation:
- If top distraction app is social media: "Instagram took {X} min this week. Maybe try putting it in a different room during focus blocks?"
- If trend is improving: "Whatever you did on {best_focus_day} worked — try to recreate those conditions."
- If trend is declining: "Rest is productive too. Consider a lighter schedule next week."

## Rules

- Total message: 3-4 sentences max
- Lead with validation, not metrics
- ONE actionable takeaway (not a list of improvements)
- Never compare to previous weeks negatively
- Celebrate small wins explicitly

## Error Handling

If backend is unreachable:
- Reply: "Couldn't pull your weekly data. Take a moment to reflect: what went well this week? What's one thing you'd adjust?"
```

**Step 2: Commit**

```bash
git add openclaw-skills/weekly-review/
git commit -m "feat(phase8): add weekly-review OpenClaw skill"
```

---

### Task 8: Create HEARTBEAT.md

**Files:**
- Create: `openclaw-skills/HEARTBEAT.md`

**Step 1: Create HEARTBEAT configuration**

Create `openclaw-skills/HEARTBEAT.md`:

```markdown
## Every morning at 7:30 AM:
- Fetch Whoop morning briefing from http://localhost:8420/whoop/morning-briefing
- Deliver formatted ADHD morning briefing to user using the morning-briefing skill
- If the fetch fails, send fallback: "Couldn't fetch your Whoop data this morning. Start with 25-min focus blocks and check in with yourself."

## Every 30 minutes during active hours (9 AM - 10 PM):
- Fetch current insights from http://localhost:8420/insights/current
- Only message the user if:
  - behavioral_state is "distracted" AND distraction_ratio > 0.5
  - OR hyperfocus_detected is true AND current_streak_minutes > 180
- Use the focus-check skill to format the message
- Do NOT message if everything looks normal — avoid notification fatigue

## Every Sunday at 8 PM:
- Fetch weekly review from http://localhost:8420/insights/weekly
- Deliver formatted weekly ADHD pattern summary using the weekly-review skill
```

**Step 2: Commit**

```bash
git add openclaw-skills/HEARTBEAT.md
git commit -m "feat(phase8): add HEARTBEAT.md scheduling config"
```

---

### Task 9: Install and Configure OpenClaw

**Step 1: Install OpenClaw**

```bash
npm install -g @anthropic-ai/openclaw
```

**Step 2: Initialize OpenClaw in the project**

```bash
cd /Users/avuthegreat/Downloads/FYP-Antigravity-OpenClaw
openclaw init --skills-dir ./openclaw-skills
```

**Step 3: Configure Telegram connector**

Follow OpenClaw docs to:
1. Create a Telegram bot via @BotFather
2. Get the bot token
3. Configure in OpenClaw settings

**Step 4: Configure WhatsApp connector**

Follow OpenClaw docs to:
1. Set up Meta Business account
2. Configure WhatsApp Business API
3. Link to OpenClaw

**Step 5: Test the connection**

```bash
openclaw test --skill adhd-vent --input "I'm feeling overwhelmed today"
```

Expected: Backend processes the message and returns a coaching response.

**Step 6: Commit any config files**

```bash
git add openclaw-skills/
git commit -m "feat(phase8): configure OpenClaw with Telegram + WhatsApp"
```

---

### Task 10: End-to-End Verification

**Step 1: Start the backend**

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port 8420 --reload
```

**Step 2: Test each endpoint manually**

```bash
# Current insights
curl http://localhost:8420/insights/current | python -m json.tool

# Daily insights
curl http://localhost:8420/insights/daily | python -m json.tool

# Weekly insights
curl http://localhost:8420/insights/weekly | python -m json.tool

# Chat/vent
curl -X POST http://localhost:8420/chat/message \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel so overwhelmed with everything", "context": {"platform": "telegram"}}' | python -m json.tool
```

**Step 3: Test via Telegram (if configured)**

Send messages to the bot:
- "I'm feeling overwhelmed today" → should get empathetic coaching response
- "How am I doing?" → should get focus check
- "Weekly review" → should get weekly summary

**Step 4: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass.

**Step 5: Final commit**

```bash
git commit -m "feat(phase8): complete OpenClaw integration with Telegram + WhatsApp"
```

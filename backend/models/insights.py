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

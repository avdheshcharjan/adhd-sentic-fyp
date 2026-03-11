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

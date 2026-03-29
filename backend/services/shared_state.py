"""
Shared singleton instances — accessible from both screen.py and insights.py.

These are in-memory, process-level singletons. In production with multiple
workers, each worker gets its own copy (acceptable for this use case since
the Swift app sends to a single process).
"""

from typing import Optional
from services.activity_classifier import ActivityClassifier
from services.adhd_metrics import ADHDMetricsEngine
from services.brain_dump_reminder import BrainDumpReminderQueue
from services.jitai_engine import JITAIEngine
from services.xai_explainer import ConceptBottleneckExplainer
from services.focus_service import FocusService
from services.focus_relevance import FocusRelevanceChecker
from models.intervention import Intervention

classifier = ActivityClassifier()
metrics_engine = ADHDMetricsEngine()
brain_dump_reminders = BrainDumpReminderQueue()
jitai_engine = JITAIEngine(brain_dump_reminders=brain_dump_reminders)
xai_explainer = ConceptBottleneckExplainer()
focus_service = FocusService()
focus_relevance = FocusRelevanceChecker()

# Pending intervention — set by screen.py when JITAI fires, cleared when acknowledged.
pending_intervention: Optional[Intervention] = None

# Off-task state — set by screen.py relevance check, polled by notch.py.
is_off_task: bool = False

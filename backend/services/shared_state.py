"""
Shared singleton instances — accessible from both screen.py and insights.py.

These are in-memory, process-level singletons. In production with multiple
workers, each worker gets its own copy (acceptable for this use case since
the Swift app sends to a single process).
"""

from services.activity_classifier import ActivityClassifier
from services.adhd_metrics import ADHDMetricsEngine
from services.brain_dump_reminder import BrainDumpReminderQueue
from services.jitai_engine import JITAIEngine
from services.xai_explainer import ConceptBottleneckExplainer
from services.focus_service import FocusService

classifier = ActivityClassifier()
metrics_engine = ADHDMetricsEngine()
brain_dump_reminders = BrainDumpReminderQueue()
jitai_engine = JITAIEngine(brain_dump_reminders=brain_dump_reminders)
xai_explainer = ConceptBottleneckExplainer()
focus_service = FocusService()

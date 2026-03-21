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
from services.focus_service import FocusService

classifier = ActivityClassifier()
metrics_engine = ADHDMetricsEngine()
jitai_engine = JITAIEngine()
xai_explainer = ConceptBottleneckExplainer()
focus_service = FocusService()

import uuid
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ActivityLog(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_name = Column(String, index=True, nullable=False)
    window_title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    category = Column(String, index=True, nullable=False)
    is_idle = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    metrics = Column(JSONB, nullable=False, default={})


class SenticAnalysis(Base):
    __tablename__ = "senticnet_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    source = Column(String, nullable=False) # e.g. "chat_message", "journal"
    timestamp = Column(DateTime(timezone=True), default=utc_now)
    
    # SenticNet specific fields
    emotion_profile = Column(JSONB, nullable=False) # Primary & secondary emotions
    safety_flags = Column(JSONB, nullable=False)    # Toxicity, depression
    adhd_signals = Column(JSONB, nullable=False)    # Frustration, overwhelmed


class InterventionHistory(Base):
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    intervention_type = Column(String, nullable=False) # e.g., "blocker", "break_suggestion"
    trigger_reason = Column(String, nullable=False)
    user_response = Column(String, nullable=True) # e.g., "accepted", "dismissed", "ignored"
    effectiveness_score = Column(Float, nullable=True) # Computed later (-1.0 to 1.0)
    context_data = Column(JSONB, default={})


class WhoopLog(Base):
    __tablename__ = "whoop_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(String, unique=True, index=True, nullable=False) # YYYY-MM-DD
    recovery_score = Column(Float, nullable=False)
    sleep_score = Column(Float, nullable=False)
    strain_score = Column(Float, nullable=False)
    metrics = Column(JSONB, nullable=False) # HRV, RHR, stages


class FocusTask(Base):
    __tablename__ = "focus_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    progress = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class BehavioralPattern(Base):
    __tablename__ = "behavioral_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_type = Column(String, index=True, nullable=False) # e.g., "procrastination_trigger", "peak_focus_time"
    description = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utc_now)
    confidence = Column(Float, default=1.0)
    embedding = Column(Vector(1536), nullable=True) # text-embedding-3-small generates 1536 dim vectors
    source_evidence = Column(JSONB, default=[]) # UUIDs to other tables or raw text


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(String, unique=True, index=True, nullable=False)  # YYYY-MM-DD

    # Core metrics
    total_active_minutes = Column(Float, nullable=False, default=0.0)
    total_focus_minutes = Column(Float, nullable=False, default=0.0)
    total_distraction_minutes = Column(Float, nullable=False, default=0.0)
    focus_percentage = Column(Float, nullable=False, default=0.0)
    distraction_percentage = Column(Float, nullable=False, default=0.0)
    context_switches = Column(Integer, nullable=False, default=0)

    # Interventions
    interventions_triggered = Column(Integer, nullable=False, default=0)
    interventions_accepted = Column(Integer, nullable=False, default=0)

    # Rich data (JSON blobs)
    top_apps = Column(JSONB, nullable=False, default=[])          # [{app_name, category, minutes, percentage}]
    behavioral_states = Column(JSONB, nullable=False, default={})  # {state: minutes}
    focus_timeline = Column(JSONB, nullable=False, default=[])     # [{category, duration}]
    emotion_scores = Column(JSONB, nullable=True)                  # {pleasantness, attention, sensitivity, aptitude}

    # Whoop (nullable — may not be available)
    whoop_recovery = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)

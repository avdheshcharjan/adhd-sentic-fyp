"""Pydantic v2 models for Brain Dump feature."""

from pydantic import BaseModel, Field
from datetime import datetime


class BrainDumpRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None  # Active focus session ID, if any


class BrainDumpResponse(BaseModel):
    id: str
    status: str  # "captured"
    emotional_state: str | None = None
    timestamp: datetime


class BrainDumpReviewItem(BaseModel):
    id: str
    content: str
    emotional_state: str | None
    timestamp: datetime
    session_id: str | None


class BrainDumpReviewResponse(BaseModel):
    items: list[BrainDumpReviewItem]
    count: int

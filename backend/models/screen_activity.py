"""Pydantic models for screen activity input/output."""

from datetime import datetime
from pydantic import BaseModel, Field
from .intervention import Intervention


class ScreenActivityInput(BaseModel):
    """Input received from the Swift menu bar app every ~2 seconds."""

    app_name: str
    window_title: str
    url: str | None = None
    is_idle: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


class ScreenActivityResponse(BaseModel):
    """Response returned to the Swift app with classification + metrics."""

    category: str
    metrics: dict
    intervention: Intervention | None = None

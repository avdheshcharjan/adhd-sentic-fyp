"""
Evaluation data logger for FYP evaluation.

Logs all chat interactions in a structured format for:
1. Ablation analysis (with vs without SenticNet)
2. Persona simulation analysis
3. Within-subjects study data collection
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class EvaluationLogEntry(BaseModel):
    timestamp: str
    conversation_id: str
    session_id: str                    # Groups interactions within one evaluation session
    ablation_mode: bool                # True = SenticNet disabled
    persona_id: Optional[str] = None   # Set when running LLM persona simulation

    # Input
    user_message: str

    # SenticNet output (null when ablation_mode=True)
    sentic_polarity: Optional[float] = None
    sentic_mood_tags: Optional[list[str]] = None
    hourglass_pleasantness: Optional[float] = None
    hourglass_attention: Optional[float] = None
    hourglass_sensitivity: Optional[float] = None
    hourglass_aptitude: Optional[float] = None

    # LLM output
    llm_response: str
    llm_latency_ms: float
    llm_token_count: int

    # Memory context used
    memory_context_summary: Optional[str] = None


class EvaluationLogger:
    def __init__(self, log_dir: str = "data/evaluation_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    async def log(self, entry: EvaluationLogEntry) -> None:
        """Append a log entry as a JSON line to the session log file."""
        filename = f"{entry.session_id}.jsonl"
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def load_session(self, session_id: str) -> list[EvaluationLogEntry]:
        """Load all entries for a given evaluation session."""
        filepath = os.path.join(self.log_dir, f"{session_id}.jsonl")
        entries = []
        with open(filepath, "r") as f:
            for line in f:
                entries.append(EvaluationLogEntry.model_validate_json(line.strip()))
        return entries

"""
Enhanced evaluation logger for the ADHD Second Brain pipeline.

Captures per-interaction metrics in JSONL format for:
- Ablation analysis (with vs without SenticNet)
- Persona simulation analysis
- Within-subjects study data collection
- Post-hoc performance analysis

Log format: JSONL (one JSON object per line)
Load with: pandas.read_json(path, lines=True)

Enabled when settings.EVALUATION_LOGGING = True.
"""

import os
import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger("adhd-brain.eval_logger")


class EvaluationLogEntry(BaseModel):
    # Identity
    timestamp: str                          # ISO 8601
    conversation_id: str
    session_id: str                         # Groups interactions within one eval session
    ablation_mode: bool                     # True = SenticNet disabled
    persona_id: Optional[str] = None        # Set during LLM persona simulation

    # Input
    user_message: str
    user_message_length: int = 0            # char count
    user_message_word_count: int = 0

    # SenticNet output (all null when ablation_mode=True)
    sentic_polarity: Optional[float] = None
    sentic_mood_tags: Optional[list[str]] = None
    hourglass_pleasantness: Optional[float] = None
    hourglass_attention: Optional[float] = None
    hourglass_sensitivity: Optional[float] = None
    hourglass_aptitude: Optional[float] = None
    sentic_latency_ms: Optional[float] = None

    # Classification context (if screen monitor active)
    active_app: Optional[str] = None
    active_title: Optional[str] = None
    classification_result: Optional[str] = None     # productive/neutral/distracting
    classification_tier: Optional[str] = None       # rules/embeddings/cache
    classification_confidence: Optional[float] = None
    classification_latency_ms: Optional[float] = None

    # Memory context
    memories_retrieved_count: int = 0
    memory_retrieval_latency_ms: Optional[float] = None
    memory_context_summary: Optional[str] = None

    # LLM output
    llm_response: str = ""
    llm_response_length: int = 0
    llm_response_token_count: int = 0
    llm_ttft_ms: Optional[float] = None
    llm_generation_ms: Optional[float] = None
    llm_tokens_per_second: Optional[float] = None
    llm_thinking_mode: Optional[str] = None         # "think" or "no_think"

    # Pipeline totals
    pipeline_total_ms: float = 0.0
    safety_input_triggered: bool = False
    safety_output_triggered: bool = False

    # System state snapshot
    system_memory_rss_mb: Optional[float] = None
    system_cpu_percent: Optional[float] = None


class EvaluationLogger:
    def __init__(self, log_dir: str = "data/evaluation_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    async def log(self, entry: EvaluationLogEntry) -> None:
        """Append entry as JSON line. Fire-and-forget safe."""
        filename = f"{entry.session_id}.jsonl"
        filepath = os.path.join(self.log_dir, filename)
        try:
            with open(filepath, "a") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.warning(f"Failed to write evaluation log: {e}")

    def load_session(self, session_id: str) -> list[EvaluationLogEntry]:
        """Load all entries for a session."""
        filepath = os.path.join(self.log_dir, f"{session_id}.jsonl")
        entries: list[EvaluationLogEntry] = []
        with open(filepath, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(EvaluationLogEntry.model_validate_json(line.strip()))
        return entries

    def load_all(self) -> list[EvaluationLogEntry]:
        """Load all entries across all sessions."""
        entries: list[EvaluationLogEntry] = []
        for f in sorted(os.listdir(self.log_dir)):
            if f.endswith(".jsonl"):
                session_id = f.replace(".jsonl", "")
                entries.extend(self.load_session(session_id))
        return entries

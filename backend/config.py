"""
Configuration management using pydantic-settings.
Reads from .env file with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://adhd:adhd@localhost:5433/adhd_brain"

    # ── SenticNet APIs (13 keys) ─────────────────────────
    SENTIC_CONCEPT_PARSING: str = ""
    SENTIC_SUBJECTIVITY: str = ""
    SENTIC_POLARITY: str = ""
    SENTIC_INTENSITY: str = ""
    SENTIC_EMOTION: str = ""
    SENTIC_ASPECT: str = ""
    SENTIC_PERSONALITY: str = ""
    SENTIC_SARCASM: str = ""
    SENTIC_DEPRESSION: str = ""
    SENTIC_TOXICITY: str = ""
    SENTIC_ENGAGEMENT: str = ""
    SENTIC_WELLBEING: str = ""
    SENTIC_ENSEMBLE: str = ""

    # ── Whoop API (OAuth 2.0) ───────────────────────────
    WHOOP_CLIENT_ID: str = ""
    WHOOP_CLIENT_SECRET: str = ""
    WHOOP_REDIRECT_URI: str = "http://localhost:8420/whoop/callback"

    # ── Google Calendar API (OAuth 2.0) ───────────────
    GOOGLE_CALENDAR_CLIENT_ID: str = ""
    GOOGLE_CALENDAR_CLIENT_SECRET: str = ""
    GOOGLE_CALENDAR_REDIRECT_URI: str = "http://localhost:8420/api/auth/google/callback"

    # ── LLM Keys ────────────────────────────────────────
    CLAUDE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ── MLX On-Device LLM ─────────────────────────────────
    MLX_PRIMARY_MODEL: str = "mlx-community/Qwen3-4B-4bit"
    MLX_LIGHT_MODEL: str = "mlx-community/Qwen3-1.7B-4bit"
    MLX_ADAPTER_PATH: str | None = None
    MLX_KEEP_ALIVE_SECONDS: int = 120
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Application Settings ────────────────────────────
    APP_PORT: int = 8420
    APP_VERSION: str = "0.1.0"
    INTERVENTION_COOLDOWN_SECONDS: int = 300
    LOG_LEVEL: str = "INFO"
    # Toggle external SenticNet API usage (requires user consent). If False,
    # the backend will skip calling SenticNet and use local fallbacks.
    SENTICNET_ENABLED: bool = True

    # ── Evaluation / Ablation Settings ─────────────────
    ABLATION_MODE: bool = False               # When True, disables SenticNet in chat pipeline
    EVALUATION_LOGGING: bool = False          # When True, logs all interactions for analysis
    EVALUATION_LOG_PATH: str = "data/evaluation_logs/"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

"""
Configuration management using pydantic-settings.
Reads from .env file with sensible defaults for local development.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://adhd:adhd@localhost:5432/adhd_brain"

    # ── SenticNet Cloud API ─────────────────────────────
    SENTICNET_API_KEY: str = ""
    SENTICNET_BASE_URL: str = "https://api.sentic.net"

    # ── Whoop API (OAuth 2.0) ───────────────────────────
    WHOOP_CLIENT_ID: str = ""
    WHOOP_CLIENT_SECRET: str = ""
    WHOOP_REDIRECT_URI: str = "http://localhost:8420/whoop/callback"

    # ── LLM Keys ────────────────────────────────────────
    CLAUDE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # ── Application Settings ────────────────────────────
    APP_PORT: int = 8420
    APP_VERSION: str = "0.1.0"
    INTERVENTION_COOLDOWN_SECONDS: int = 300
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

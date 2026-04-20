"""
OMA Agent — Configuration (Module 02)
Loads settings from .env using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenRouter / LLM ──────────────────────────────────────────
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "deepseek/deepseek-r1:free"

    # ── Application ──────────────────────────────────────────────
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    app_title: str = "OMA Agent"
    app_version: str = "0.1.0"


# Singleton — import `settings` anywhere in the project
settings = Settings()

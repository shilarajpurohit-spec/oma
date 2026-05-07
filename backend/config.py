"""
OMA Agent — Configuration (Module 02)
Loads settings from .env using pydantic-settings.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenRouter / LLM ──────────────────────────────────────────
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_base_url: str = ""
    llm_model: str = "deepseek/deepseek-r1:free"

    @model_validator(mode="after")
    def normalize_api_settings(self):
        if not self.openrouter_api_key:
            self.openrouter_api_key = self.llm_api_key
        if not self.openrouter_base_url:
            self.openrouter_base_url = self.llm_base_url
        return self

    # ── Application ──────────────────────────────────────────────
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    app_title: str = "OMA Agent"
    app_version: str = "0.1.0"


# Singleton — import `settings` anywhere in the project
settings = Settings()

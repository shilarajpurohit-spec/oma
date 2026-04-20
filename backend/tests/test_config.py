"""
Tests for backend.config (Module 02)
"""




class TestSettings:
    """Test the Settings configuration class."""

    def test_default_settings_load(self):
        """Settings should load with defaults even without .env."""
        from backend.config import Settings

        s = Settings()
        assert s.app_title == "OMA Agent"
        assert s.app_version == "0.1.0"
        assert s.app_env == "development"
        assert s.host == "0.0.0.0"
        assert s.port == 8000

    def test_openrouter_defaults(self):
        """OpenRouter fields should have sensible defaults."""
        from backend.config import Settings

        s = Settings()
        assert s.openrouter_base_url == "https://openrouter.ai/api/v1"
        assert s.llm_model == "deepseek/deepseek-r1:free"

    def test_env_override(self, monkeypatch):
        """Environment variables should override defaults."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")

        from backend.config import Settings

        s = Settings()
        assert s.app_env == "production"
        assert s.port == 9000
        assert s.openrouter_api_key == "test-key-123"

    def test_singleton_import(self):
        """The `settings` singleton should be importable."""
        from backend.config import settings

        assert settings is not None
        assert settings.app_title == "OMA Agent"

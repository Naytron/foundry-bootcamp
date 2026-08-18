"""Application configuration and environment validation."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables and an optional local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    use_mock_services: bool = True

    foundry_project_endpoint: HttpUrl | None = None
    foundry_model: str | None = None
    embedding_model: str | None = None
    azure_ai_search_endpoint: HttpUrl | None = None
    azure_ai_search_index: str = "support-knowledge"
    azure_client_id: str | None = None
    applicationinsights_connection_string: SecretStr | None = None

    bootcamp_access_token: SecretStr = SecretStr("local-development-token")
    max_message_characters: int = Field(default=4_000, ge=100, le=20_000)
    max_sessions: int = Field(default=100, ge=1, le=10_000)
    session_ttl_seconds: int = Field(default=3_600, ge=60, le=86_400)
    rate_limit_requests: int = Field(default=30, ge=1, le=10_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3_600)

    @model_validator(mode="after")
    def validate_cloud_configuration(self) -> Self:
        """Require cloud values only when the mock providers are disabled."""
        if self.use_mock_services:
            return self

        required = {
            "FOUNDRY_PROJECT_ENDPOINT": self.foundry_project_endpoint,
            "FOUNDRY_MODEL": self.foundry_model,
            "AZURE_AI_SEARCH_ENDPOINT": self.azure_ai_search_endpoint,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            joined = ", ".join(sorted(missing))
            raise ValueError(f"Missing required cloud configuration: {joined}")

        if (
            self.app_env == "production"
            and self.bootcamp_access_token.get_secret_value() == "local-development-token"
        ):
            raise ValueError("BOOTCAMP_ACCESS_TOKEN must be changed in production")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()

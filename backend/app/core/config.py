"""Application settings loaded from environment variables and an optional local .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    """Validated runtime configuration shared by the API and future workers."""

    app_name: str = "AI Market Intelligence API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    mongodb_uri: SecretStr | None = None
    database_name: str = "ai_market_intelligence"
    market_data_api_key: SecretStr | None = None
    news_api_key: SecretStr | None = None
    economic_data_api_key: SecretStr | None = None
    api_cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("API_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    request_timeout_seconds: int = Field(default=15, ge=1, le=120)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, value: object) -> str:
        normalized = str(value).upper()
        if normalized not in VALID_LOG_LEVELS:
            allowed = ", ".join(sorted(VALID_LOG_LEVELS))
            raise ValueError(f"LOG_LEVEL must be one of: {allowed}")
        return normalized

    @field_validator("api_cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("API_CORS_ORIGINS must include at least one origin")

        for origin in origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("Each API_CORS_ORIGINS entry must be an HTTP(S) origin")
            if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
                raise ValueError("API_CORS_ORIGINS entries must not include paths, queries, or fragments")

        return ",".join(origins)

    @property
    def cors_origins(self) -> tuple[str, ...]:
        """Return CORS origins in the form expected by FastAPI middleware."""
        return tuple(self.api_cors_origins.split(","))


@lru_cache
def get_settings() -> Settings:
    """Create one validated settings object per process."""
    return Settings()
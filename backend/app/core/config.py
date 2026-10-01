"""Application settings loaded from environment variables and an optional local .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
# Locally the backend lives below the repository root. In the container the
# backend is copied directly to /app, so use that directory instead of relying
# on a fixed number of parents.
PROJECT_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT.parent / ".env.example").exists() else BACKEND_ROOT
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    """Validated runtime configuration shared by the API and future workers."""

    app_name: str = "AI Market Intelligence API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    mongodb_uri: SecretStr | None = None
    database_name: str = Field(default="ai_market_intelligence", min_length=1, max_length=63)
    mongodb_server_selection_timeout_ms: int = Field(default=5000, ge=1000, le=60000)
    news_api_key: SecretStr | None = None
    economic_data_api_key: SecretStr | None = None
    trading_economics_api_key: SecretStr | None = None
    financecalendar_enabled: bool = True
    financecalendar_base_url: str = "https://www.financecalendar.com/wp-json/fc/v1"
    twelve_data_api_key: SecretStr | None = None
    marketaux_api_key: SecretStr | None = None
    fred_api_key: SecretStr | None = None
    bea_api_key: SecretStr | None = None
    eodhd_api_key: SecretStr | None = None
    bls_api_key: SecretStr | None = None
    api_cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("API_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    request_timeout_seconds: int = Field(default=15, ge=1, le=120)
    models_dir: Path = Field(default=PROJECT_ROOT / "data" / "models")
    model_schema_version: str = "1.0"
    market_ingestion_enabled: bool = False
    market_ingestion_interval_seconds: int = Field(default=3600, ge=60, le=86400)
    market_ingestion_limit: int = Field(default=300, ge=2, le=5000)
    market_ingestion_symbols: str = "XAUUSD"
    market_ingestion_timeframe: str = "1h"

    # Live market service configuration
    live_reconnect_base_seconds: int = Field(default=1, ge=1, description="Base seconds for exponential backoff")
    live_reconnect_max_seconds: int = Field(default=30, ge=1, description="Maximum backoff seconds")
    live_freshness_live_sec: int = Field(default=5, ge=1, description="Freshness threshold for LIVE status (seconds)")
    live_freshness_delayed_sec: int = Field(default=30, ge=1, description="Freshness threshold for DELAYED status (seconds)")

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

    @field_validator("mongodb_uri", mode="before")
    @classmethod
    def validate_mongodb_uri(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        uri = str(value).strip()
        if not uri:
            return None
        if not uri.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MONGODB_URI must start with mongodb:// or mongodb+srv://")
        return uri

    @field_validator("database_name")
    @classmethod
    def validate_database_name(cls, value: str) -> str:
        if any(character in value for character in ("/", "\\", ".", "\"", "$", "\x00")):
            raise ValueError("DATABASE_NAME contains unsupported MongoDB database-name characters")
        return value

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

    @property
    def mongodb_uri_value(self) -> str | None:
        """Return the connection URI only for the database client; never log it."""
        if self.mongodb_uri is None:
            return None
        return self.mongodb_uri.get_secret_value()

    @property
    def ingestion_symbols(self) -> tuple[str, ...]:
        return tuple(value.strip().upper() for value in self.market_ingestion_symbols.split(",") if value.strip())


@lru_cache
def get_settings() -> Settings:
    """Create one validated settings object per process."""
    return Settings()

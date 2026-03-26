"""Base configuration shared across all services."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings class — each service subclasses with its own env_prefix."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Shared settings
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    openai_api_key: str = ""

    # Service identity (overridden per service)
    service_name: str = "unknown"
    service_version: str = "0.1.0"

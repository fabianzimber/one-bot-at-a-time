"""Base configuration shared across all services."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings class — each service subclasses with its own env_prefix.

    Shared fields use validation_alias with AliasChoices so they are read from
    the unprefixed env var (LOG_LEVEL, CORS_ORIGINS, OPENAI_API_KEY) regardless
    of the subclass's env_prefix.  The prefixed variant (e.g. CHAT_LOG_LEVEL)
    is still accepted as a service-specific override.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Shared settings — unprefixed env vars take priority
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("log_level", "LOG_LEVEL"),
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"),
    )
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("openai_api_key", "OPENAI_API_KEY"),
    )

    # Service identity (overridden per service)
    service_name: str = "unknown"
    service_version: str = "0.1.0"

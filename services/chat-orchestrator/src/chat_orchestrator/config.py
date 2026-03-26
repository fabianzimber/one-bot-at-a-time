"""Chat Orchestrator configuration."""

from pydantic_settings import SettingsConfigDict

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CHAT_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    service_name: str = "chat-orchestrator"

    # LLM
    llm_model: str = "gpt-4o"
    llm_fallback_model: str = "gpt-4o-mini"
    llm_emergency_model: str = "gpt-3.5-turbo"

    # Internal service URLs
    rag_service_url: str = "http://localhost:8002"
    hr_service_url: str = "http://localhost:8003"

    # Redis
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()

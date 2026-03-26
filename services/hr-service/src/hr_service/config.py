"""HR Service configuration."""

from pydantic_settings import SettingsConfigDict

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HR_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    service_name: str = "hr-service"

    # Database — SQLite for local dev, PostgreSQL for production
    database_url: str = "sqlite+aiosqlite:///./hr_data.db"

    # Seed data
    seed_employee_count: int = 50


settings = Settings()

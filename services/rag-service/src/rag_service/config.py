"""RAG Service configuration."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from shared.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAG_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    service_name: str = "rag-service"

    # Storage
    vector_backend: str = "chroma"
    database_url: str = "sqlite+aiosqlite:///./rag_data.db"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8004
    chroma_collection: str = "trenkwalder_docs"

    # Embedding
    embedding_model: str = "text-embedding-3-small"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Upload limits
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = Field(default=[".pdf", ".txt", ".md", ".docx"])


settings = Settings()

"""Database models for the RAG service."""

from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DocumentRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    filename: str = Field(index=True)
    chunk_count: int
    uploaded_at: datetime


class DocumentChunkRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    document_id: str = Field(foreign_key="documentrecord.id", index=True)
    source_file: str
    page_number: int | None = Field(default=None, index=True)
    chunk_index: int = Field(index=True)
    chunk_text: str
    embedding: list[float] = Field(sa_column=Column(JSON))

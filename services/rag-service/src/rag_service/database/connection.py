"""Database connection and session management for the RAG service."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from rag_service.config import settings

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_init_lock = asyncio.Lock()


async def init_database(database_url: str) -> None:
    global _engine, _session_factory

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _engine = create_async_engine(database_url, echo=False, future=True, connect_args=connect_args)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("RAG database initialized", extra={"url": database_url})


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("RAG database not initialized")
    return _session_factory


async def ensure_database_ready() -> None:
    if _session_factory is not None:
        return

    async with _init_lock:
        if _session_factory is not None:
            return
        await init_database(settings.database_url)


async def get_session() -> AsyncGenerator[AsyncSession]:
    await ensure_database_ready()
    async with get_session_factory() as session:
        yield session


async def close_database() -> None:
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_factory = None
    logger.info("RAG database connection closed")

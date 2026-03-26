"""Database connection and engine setup."""

import logging

logger = logging.getLogger(__name__)


async def init_database(database_url: str) -> None:
    """Initialize the database engine and create tables.

    Local dev: SQLite + aiosqlite
    Production: PostgreSQL + asyncpg
    """
    # TODO: Implement with SQLModel
    # from sqlmodel import SQLModel, create_engine
    # engine = create_engine(database_url)
    # SQLModel.metadata.create_all(engine)
    logger.info("Database initialization stub", extra={"url": database_url})


async def close_database() -> None:
    """Close database connections."""
    # TODO: Dispose engine
    logger.info("Database connection closed (stub)")

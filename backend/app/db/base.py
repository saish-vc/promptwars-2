"""Async SQLAlchemy engine and session factory.

Supports two modes:
- **Production**: AsyncPG driver against PostgreSQL (with pgvector extension).
- **Fallback**: aiosqlite against local SQLite when ``ENABLE_FALLBACK_MODE=true``.

Usage::

    async with get_session() as session:
        result = await session.execute(select(Document))
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────

def _build_engine_url() -> str:
    """Return the SQLAlchemy async database URL.

    Falls back to SQLite when fallback mode is enabled.
    """
    if settings.enable_fallback_mode:
        sqlite_url = f"sqlite+aiosqlite:///{settings.database_path}"
        logger.info("Fallback mode — using SQLite: %s", sqlite_url)
        return sqlite_url
    return settings.postgres_url


_engine_url = _build_engine_url()

# Pool settings differ between PostgreSQL and SQLite
if "sqlite" in _engine_url:
    _engine = create_async_engine(
        _engine_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    _engine = create_async_engine(
        _engine_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

# ── Session factory ───────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager that yields a database session and commits on exit.

    Rolls back automatically on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables() -> None:
    """Create all ORM-mapped tables if they do not already exist.

    Used on startup when Alembic is not managing migrations (e.g., local dev).
    In production, run ``alembic upgrade head`` instead.
    """
    from app.db.models import Base  # noqa: PLC0415 — local import avoids circular

    async with _engine.begin() as conn:
        # Enable pgvector extension on PostgreSQL before creating tables
        if "postgresql" in _engine_url:
            await conn.execute(
                __import__("sqlalchemy", fromlist=["text"]).text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                )
            )
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")


async def dispose_engine() -> None:
    """Dispose the async engine connection pool (call on app shutdown)."""
    await _engine.dispose()
    logger.info("Database engine disposed")

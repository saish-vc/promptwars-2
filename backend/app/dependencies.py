"""FastAPI dependency injection factories.

Use these with ``Depends()`` in route handlers::

    @router.get("/example")
    async def example(
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ):
        ...

All dependencies are request-scoped unless noted.

``get_redis_client()`` is also called directly (without Depends) by services
such as the PromptCache and EmbeddingService that cannot use FastAPI's DI system.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ── Redis singleton pool ───────────────────────────────────────────────────────

_redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialise the shared Redis connection pool (called on app startup)."""
    global _redis_pool
    if not settings.redis_configured:
        logger.info("Redis not configured — caching is disabled")
        return
    try:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
            max_connections=20,
        )
        # Verify connection
        await _redis_pool.ping()
        logger.info("Redis connection pool initialised: %s", settings.redis_url)
    except Exception as exc:
        logger.warning("Redis connection failed — caching disabled: %s", exc)
        _redis_pool = None


async def close_redis() -> None:
    """Close the Redis connection pool (called on app shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("Redis connection pool closed")


async def get_redis_client() -> aioredis.Redis | None:
    """Return the shared Redis client, or ``None`` when Redis is unavailable.

    Can be called directly by services (not only via FastAPI Depends).
    """
    return _redis_pool


# ── FastAPI dependency: database session ─────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a SQLAlchemy async session per request.

    Commits on success, rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── FastAPI dependency: Redis ─────────────────────────────────────────────────


async def get_redis() -> aioredis.Redis | None:
    """Yield the shared Redis client (or None if unconfigured)."""
    return _redis_pool


# ── FastAPI dependency: blob storage ─────────────────────────────────────────


async def get_blob_storage():
    """Return the active BlobStorageService (S3 or local fallback)."""
    from app.services.documents import blob_storage

    return blob_storage


# ── FastAPI dependency: document store ───────────────────────────────────────


async def get_document_store():
    """Return the AsyncDocumentStore singleton."""
    from app.services.documents import get_async_store

    return get_async_store()

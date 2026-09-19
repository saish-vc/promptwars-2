"""Embedding service — generates dense vector representations of text.

Uses the NVIDIA NIM Embeddings API (``nvidia/nv-embedqa-e5-v5`` by default).
Results are cached in Redis to avoid redundant API calls.

When ``EMBEDDING_ENABLED=false`` or Redis is unavailable, the service
returns ``None`` and callers should fall back to keyword search.
"""

from __future__ import annotations

import hashlib
import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates and caches text embeddings via NVIDIA NIM.

    Caching strategy:
    - Cache key: ``embedding:<sha256(text)>``
    - TTL: ``settings.cache_ttl_seconds`` (default 24 h)
    - Cache miss → NIM API call → cache result → return
    - When Redis is unavailable: calls API directly without caching.
    """

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=settings.nim_base_url,
                timeout=60.0,
            )
        return self._http

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"embedding:{digest}"

    async def _get_cached(self, key: str) -> list[float] | None:
        """Retrieve embedding from Redis cache."""
        if not settings.redis_configured:
            return None
        try:
            from app.dependencies import get_redis_client

            redis = await get_redis_client()
            raw = await redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug("Redis cache get failed: %s", exc)
        return None

    async def _set_cached(self, key: str, vector: list[float]) -> None:
        """Store embedding in Redis cache with TTL."""
        if not settings.redis_configured:
            return
        try:
            from app.dependencies import get_redis_client

            redis = await get_redis_client()
            await redis.set(key, json.dumps(vector), ex=settings.cache_ttl_seconds)
        except Exception as exc:
            logger.debug("Redis cache set failed: %s", exc)

    async def embed(self, text: str) -> list[float] | None:
        """Generate an embedding vector for the given text.

        Returns:
            A list of floats (length = ``settings.embedding_dim``),
            or ``None`` if embeddings are disabled or the API call fails.
        """
        if not settings.embedding_active:
            return None

        if not settings.nim_api_key:
            logger.warning("EMBEDDING_ENABLED=true but NIM_API_KEY is not set")
            return None

        cache_key = self._cache_key(text)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            logger.debug("Embedding cache hit for key=%s", cache_key[:16])
            return cached

        try:
            http = await self._get_http()
            response = await http.post(
                "/embeddings",
                json={
                    "model": settings.embedding_model,
                    "input": [text],
                    "encoding_format": "float",
                },
                headers={
                    "Authorization": f"Bearer {settings.nim_api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            vector: list[float] = data["data"][0]["embedding"]
        except Exception as exc:
            logger.warning("Embedding API call failed: %s", exc)
            return None

        await self._set_cached(cache_key, vector)
        return vector

    async def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Generate embeddings for multiple texts concurrently."""
        import asyncio

        return list(await asyncio.gather(*[self.embed(t) for t in texts]))


# Singleton
embedding_service = EmbeddingService()

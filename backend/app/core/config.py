"""Application settings loaded from environment variables via pydantic-settings.

All settings have sensible defaults so the app can run locally without
a full Docker Compose stack when ``ENABLE_FALLBACK_MODE=true``.
"""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Typed, validated application configuration.

    Values are read from environment variables (case-insensitive).
    A ``.env`` file in the working directory is automatically loaded.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ────────────────────────────────────────────────
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: str | list[str] = ["http://localhost:5173"]
    gunicorn_workers: int = 4

    # ── Upload ────────────────────────────────────────────────
    max_upload_bytes: int = 10_485_760  # 10 MB

    # ── LLM providers ─────────────────────────────────────────
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    nim_api_key: str = ""
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"

    # ── PostgreSQL ────────────────────────────────────────────
    postgres_url: str = "postgresql+asyncpg://legiflow:legiflow@localhost:5432/legiflow"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = ""
    cache_ttl_seconds: int = 86_400  # 24 h

    # ── S3 / MinIO blob storage ───────────────────────────────
    s3_endpoint_url: str = ""
    s3_bucket_name: str = "legiflow"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "us-east-1"

    # ── Embeddings ────────────────────────────────────────────
    embedding_enabled: bool = False
    embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    embedding_dim: int = 1024

    # ── Fallback / legacy ─────────────────────────────────────
    enable_fallback_mode: bool = False
    # SQLite path — only used when enable_fallback_mode=True
    database_path: str = "/tmp/legiflow.db"

    # ── Derived helpers ───────────────────────────────────────
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: str | list[str]) -> list[str]:
        """Allow comma-separated string or a list from env."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log(cls, v: str) -> str:
        return v.upper()

    @property
    def redis_configured(self) -> bool:
        """True when a Redis URL is provided."""
        return bool(self.redis_url)

    @property
    def s3_configured(self) -> bool:
        """True when S3/MinIO credentials are provided."""
        return bool(self.s3_access_key and self.s3_secret_key)

    @property
    def embedding_active(self) -> bool:
        """True when embeddings are enabled and an embedding model is set."""
        return self.embedding_enabled and bool(self.embedding_model)


settings = Settings()

# ── Startup validation warnings ───────────────────────────────
if settings.llm_provider == "groq":
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY is not set; LLM paths will fail at runtime")
    else:
        logger.info("GROQ_API_KEY configured; model=%s", settings.groq_model)
else:
    if not settings.nim_api_key:
        logger.warning("NIM_API_KEY is not set; LLM paths will fail at runtime")
    else:
        logger.info("NIM_API_KEY configured")

if not settings.redis_configured:
    logger.warning(
        "REDIS_URL not set — prompt caching and circuit breaker are disabled"
    )

if not settings.s3_configured:
    if settings.enable_fallback_mode:
        logger.info("S3 not configured — falling back to local disk storage")
    else:
        logger.warning(
            "S3 credentials not set and ENABLE_FALLBACK_MODE=false; "
            "document uploads will fail"
        )

if settings.embedding_active:
    logger.info(
        "Vector embeddings enabled; model=%s dim=%d",
        settings.embedding_model,
        settings.embedding_dim,
    )

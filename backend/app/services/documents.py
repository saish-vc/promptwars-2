"""Document storage services — text extraction, blob storage, and document persistence.

Architecture:
- ``extract_text``          — CPU-bound PDF/DOCX extraction (always wrapped in asyncio.to_thread)
- ``BlobStorageService``    — abstract interface for raw file bytes storage
- ``S3BlobStorage``         — production: stores blobs in S3/MinIO via aioboto3
- ``LocalBlobStorage``      — fallback: stores blobs as local files
- ``AsyncDocumentStore``    — stores metadata in PostgreSQL, text/blobs via BlobStorageService
- ``DocumentStore``         — legacy shim backed by AsyncDocumentStore (preserves all call sites)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document as DocxDocument
from pypdf import PdfReader
from sqlalchemy import select, text

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt"}


# ── Text extraction ───────────────────────────────────────────────────────────


def _first_line(content: bytes) -> str:
    """Best-effort first non-empty line for debugging extraction failures."""
    try:
        raw = content.decode("utf-8-sig", errors="replace")
    except Exception:
        raw = ""
    for line in raw.splitlines():
        if line.strip():
            return line[:200]
    return ""


def extract_text(filename: str, content: bytes) -> str:
    """Synchronously extract plain text from PDF, DOCX, or TXT bytes.

    This is a CPU-bound function. Always call it inside ``asyncio.to_thread``
    from async contexts::

        text = await asyncio.to_thread(extract_text, filename, content)

    Raises:
        ValueError: if the file type is unsupported, parsing fails, or the
                    document contains no extractable text.
    """
    filename = str(filename).strip() or "unknown"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError("Only PDF, DOCX, and TXT files are supported")
    try:
        if suffix == ".pdf":
            text = "\n".join(
                page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages
            )
        elif suffix == ".docx":
            text = "\n".join(
                paragraph.text
                for paragraph in DocxDocument(BytesIO(content)).paragraphs
            )
        else:  # .txt
            text = content.decode("utf-8-sig")
    except Exception as exc:
        logger.warning(
            "extract_text failed for %s: %s",
            filename,
            exc,
            extra={"filename": filename, "first_line": _first_line(content)},
        )
        raise ValueError("Could not extract text from this file") from exc
    if not text.strip():
        raise ValueError("This document contains no extractable text")
    return text.strip()


# ── Blob storage interface ────────────────────────────────────────────────────


class BlobStorageService(ABC):
    """Abstract interface for raw file blob storage."""

    @abstractmethod
    async def upload(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes and return the object key."""

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download and return bytes for the given object key."""

    @abstractmethod
    async def upload_text(self, key: str, text: str) -> str:
        """Upload UTF-8 text and return the object key."""

    @abstractmethod
    async def download_text(self, key: str) -> str:
        """Download and return UTF-8 text for the given object key."""


class S3BlobStorage(BlobStorageService):
    """S3/MinIO blob storage via aioboto3."""

    def __init__(self) -> None:
        self._bucket = settings.s3_bucket_name
        self._endpoint = settings.s3_endpoint_url or None
        self._access_key = settings.s3_access_key
        self._secret_key = settings.s3_secret_key
        self._region = settings.s3_region

    def _client(self):
        import aioboto3  # deferred import — optional dependency

        session = aioboto3.Session()
        kwargs: dict = {
            "service_name": "s3",
            "aws_access_key_id": self._access_key,
            "aws_secret_access_key": self._secret_key,
            "region_name": self._region,
        }
        if self._endpoint:
            kwargs["endpoint_url"] = self._endpoint
        return session.client(**kwargs)

    async def _ensure_bucket(self, client) -> None:
        try:
            await client.head_bucket(Bucket=self._bucket)
        except Exception:
            await client.create_bucket(Bucket=self._bucket)
            logger.info("Created S3 bucket: %s", self._bucket)

    async def upload(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        async with self._client() as client:
            await self._ensure_bucket(client)
            await client.put_object(
                Bucket=self._bucket, Key=key, Body=content, ContentType=content_type
            )
        logger.debug("S3 upload: key=%s size=%d", key, len(content))
        return key

    async def download(self, key: str) -> bytes:
        async with self._client() as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            return await response["Body"].read()

    async def upload_text(self, key: str, text: str) -> str:
        return await self.upload(key, text.encode("utf-8"), content_type="text/plain; charset=utf-8")

    async def download_text(self, key: str) -> str:
        return (await self.download(key)).decode("utf-8")


class LocalBlobStorage(BlobStorageService):
    """Local filesystem blob storage — used in fallback/dev mode."""

    def __init__(self, base_dir: str = "/tmp/legiflow_blobs") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "_")
        return self._base / safe

    async def upload(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        self._path(key).write_bytes(content)
        return key

    async def download(self, key: str) -> bytes:
        p = self._path(key)
        if not p.exists():
            raise FileNotFoundError(f"Blob not found: {key}")
        return p.read_bytes()

    async def upload_text(self, key: str, text: str) -> str:
        return await self.upload(key, text.encode("utf-8"))

    async def download_text(self, key: str) -> str:
        return (await self.download(key)).decode("utf-8")


def build_blob_storage() -> BlobStorageService:
    """Factory — returns S3BlobStorage when configured and not in fallback mode, else LocalBlobStorage."""
    if settings.s3_configured and not settings.enable_fallback_mode:
        logger.info("Using S3 blob storage (endpoint=%s)", settings.s3_endpoint_url or "AWS")
        return S3BlobStorage()
    logger.info("Using local filesystem blob storage (fallback mode)")
    return LocalBlobStorage()


# Singleton (replaced in lifespan for DI)
blob_storage: BlobStorageService = build_blob_storage()


# ── Async document store (PostgreSQL) ─────────────────────────────────────────


class AsyncDocumentStore:
    """Stores document metadata in PostgreSQL and text blobs via BlobStorageService.

    In fallback mode (SQLite), full text is stored directly in the ``text`` column.
    In production mode (PostgreSQL + S3), only a preview is stored in the DB;
    full text lives in S3.
    """

    def __init__(self, storage: BlobStorageService | None = None) -> None:
        self._storage = storage or blob_storage

    async def save(self, text: str, filename: str | None = None) -> str:
        """Persist document text and return a new ``doc_id``."""
        from app.db.base import get_session
        from app.db.models import Document

        doc_id = uuid4().hex
        preview = text[:500]

        if settings.enable_fallback_mode:
            # Store full text in DB column (SQLite-compatible)
            async with get_session() as session:
                session.add(Document(
                    doc_id=doc_id,
                    filename=filename,
                    text=text,
                    text_preview=preview,
                ))
            return doc_id

        # Production: store text in S3, metadata in PostgreSQL
        s3_key = f"documents/{doc_id}/text.txt"
        await self._storage.upload_text(s3_key, text)

        async with get_session() as session:
            session.add(Document(
                doc_id=doc_id,
                filename=filename,
                s3_key=s3_key,
                text_preview=preview,
            ))
        return doc_id

    async def get_text(self, doc_id: str) -> str | None:
        """Retrieve the full document text by ``doc_id``."""
        from app.db.base import get_session
        from app.db.models import Document

        async with get_session() as session:
            result = await session.execute(
                select(Document).where(Document.doc_id == doc_id)
            )
            doc = result.scalar_one_or_none()

        if doc is None:
            return None

        if settings.enable_fallback_mode:
            return doc.text

        if doc.s3_key:
            try:
                return await self._storage.download_text(doc.s3_key)
            except Exception as exc:
                logger.error("Failed to download text from S3 for doc_id=%s: %s", doc_id, exc)
                return None
        # Fallback: text might have been stored directly (migration scenario)
        return doc.text


# Singleton async store
_async_store: AsyncDocumentStore | None = None


def get_async_store() -> AsyncDocumentStore:
    global _async_store
    if _async_store is None:
        _async_store = AsyncDocumentStore()
    return _async_store


# ── Legacy DocumentStore shim ─────────────────────────────────────────────────


class DocumentStore:
    """Backward-compatible synchronous-looking shim over AsyncDocumentStore.

    All routers still call ``store.save()`` and ``store.get_text()`` — these
    methods now delegate to the async store and run synchronously only in the
    SQLite fallback path.  In all async FastAPI handler contexts, prefer
    calling ``await get_async_store().save(...)`` directly.

    The ``initialize()`` method is kept for lifespan compatibility.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._fallback_sqlite = settings.enable_fallback_mode

    def initialize(self) -> None:
        """Initialise storage — called in the FastAPI lifespan context.

        In fallback mode: creates SQLite DB via sync sqlite3 for immediate use.
        In production mode: tables are created by ``create_all_tables()`` in lifespan.
        """
        if self._fallback_sqlite:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS documents "
                    "(doc_id TEXT PRIMARY KEY, filename TEXT, text TEXT NOT NULL, text_preview TEXT)"
                )
                try:
                    conn.execute("ALTER TABLE documents ADD COLUMN text_preview TEXT")
                except sqlite3.OperationalError:
                    pass  # column already exists
        # Production path: async table creation is handled in app lifespan

    def save(self, text: str, filename: str | None = None) -> str:
        """Save document — sync wrapper (use only from sync or fallback contexts)."""
        if self._fallback_sqlite:
            doc_id = uuid4().hex
            with sqlite3.connect(self.path) as conn:
                preview = text[:500]
                conn.execute(
                    "INSERT INTO documents (doc_id, filename, text, text_preview) VALUES (?, ?, ?, ?)",
                    (doc_id, filename, text, preview),
                )
            return doc_id
        raise RuntimeError(
            "DocumentStore.save() is not supported in async/production mode. "
            "Use await get_async_store().save() instead."
        )

    def get_text(self, doc_id: str) -> str | None:
        """Get text — sync wrapper (use only from sync or fallback contexts)."""
        if self._fallback_sqlite:
            with sqlite3.connect(self.path) as conn:
                row = conn.execute(
                    "SELECT text FROM documents WHERE doc_id = ?", (doc_id,)
                ).fetchone()
            return row[0] if row else None
        raise RuntimeError(
            "DocumentStore.get_text() is not supported in async/production mode. "
            "Use await get_async_store().get_text() instead."
        )

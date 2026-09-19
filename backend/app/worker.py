"""ARQ background worker definitions.

Start the worker with::

    arq app.worker.WorkerSettings

Tasks:
- ``process_document_task`` — downloads raw file from S3, extracts text,
  generates chunk embeddings (if enabled), stores chunks in PostgreSQL,
  and marks the AnalysisJob as done/failed.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Task functions ────────────────────────────────────────────────────────────


async def process_document_task(
    ctx: dict,
    job_id: str,
    doc_id: str,
    s3_key: str,
    filename: str,
) -> dict:
    """Background task: extract text from a stored S3 blob and optionally embed chunks.

    Updates ``AnalysisJob`` status in PostgreSQL throughout processing.

    Args:
        ctx:      ARQ context dict (contains Redis connection).
        job_id:   UUID hex of the ``AnalysisJob`` row.
        doc_id:   UUID hex of the ``Document`` row.
        s3_key:   S3/MinIO object key of the raw uploaded file.
        filename: Original filename (used to determine extraction method).

    Returns:
        A dict ``{"doc_id": ..., "status": "done"}`` on success.
    """
    from app.db.base import get_session
    from app.db.models import AnalysisJob, JobStatus, Document, DocumentChunk
    from app.services.documents import blob_storage, extract_text
    from app.services.embeddings import embedding_service

    # ── Mark job as processing ────────────────────────────────
    async with get_session() as session:
        job = await session.get(AnalysisJob, job_id)
        if job is None:
            logger.error("process_document_task: job_id=%s not found", job_id)
            return {"error": "job not found"}
        job.status = JobStatus.processing
        await session.flush()

    try:
        # ── Download raw file from blob storage ───────────────
        logger.info("Worker: downloading blob key=%s", s3_key)
        content = await blob_storage.download(s3_key)

        # ── Extract text (CPU-bound — run in thread) ──────────
        logger.info("Worker: extracting text from %s", filename)
        text = await asyncio.to_thread(extract_text, filename, content)

        # ── Persist full text to S3 text blob ─────────────────
        text_key = f"documents/{doc_id}/text.txt"
        await blob_storage.upload_text(text_key, text)

        # ── Update Document row with text key and preview ─────
        async with get_session() as session:
            doc = await session.get(Document, doc_id)
            if doc:
                doc.s3_key = text_key  # overwrite raw-file key with text key
                doc.text_preview = text[:500]
                await session.flush()

        # ── Chunking & embedding (if enabled) ─────────────────
        chunks = _chunk_text(text)
        chunk_rows: list[DocumentChunk] = []

        for idx, chunk_text in enumerate(chunks):
            embedding = None
            if settings.embedding_active:
                try:
                    embedding = await embedding_service.embed(chunk_text)
                except Exception as emb_exc:
                    logger.warning(
                        "Worker: embedding failed for chunk %d: %s", idx, emb_exc
                    )

            chunk_rows.append(
                DocumentChunk(
                    doc_id=doc_id,
                    chunk_index=idx,
                    text=chunk_text,
                    embedding=embedding,
                )
            )

        # ── Batch-insert chunks ───────────────────────────────
        if chunk_rows:
            async with get_session() as session:
                session.add_all(chunk_rows)

        # ── Mark job done ─────────────────────────────────────
        async with get_session() as session:
            job = await session.get(AnalysisJob, job_id)
            if job:
                job.status = JobStatus.done
                job.result_json = json.dumps({"doc_id": doc_id, "chunks": len(chunks)})

        logger.info(
            "Worker: processed doc_id=%s chunks=%d", doc_id, len(chunks)
        )
        return {"doc_id": doc_id, "status": "done", "chunks": len(chunks)}

    except Exception as exc:
        logger.exception("Worker: failed to process doc_id=%s: %s", doc_id, exc)
        async with get_session() as session:
            job = await session.get(AnalysisJob, job_id)
            if job:
                job.status = JobStatus.failed
                job.error = str(exc)[:2048]
        raise


# ── Helpers ───────────────────────────────────────────────────────────────────


def _chunk_text(text: str, target_size: int = 500, overlap: int = 50) -> list[str]:
    """Split document text into overlapping chunks, preferring paragraph boundaries.

    Args:
        text:        Full document text.
        target_size: Approximate characters per chunk.
        overlap:     Characters of overlap between consecutive chunks.

    Returns:
        List of non-empty text chunks.
    """
    # Split on double newlines first (paragraph-aware)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= target_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # Para itself larger than target → split by characters with overlap
            if len(para) > target_size:
                for i in range(0, len(para), target_size - overlap):
                    piece = para[i : i + target_size].strip()
                    if piece:
                        chunks.append(piece)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


# ── Worker settings ───────────────────────────────────────────────────────────


class WorkerSettings:
    """ARQ worker configuration.

    Configure via ``REDIS_URL`` environment variable.
    """

    functions = [process_document_task]
    max_jobs = 10
    job_timeout = timedelta(minutes=10)
    keep_result = timedelta(hours=24)
    retry_jobs = True
    max_tries = 3

    @classmethod
    def redis_settings(cls):
        from arq.connections import RedisSettings as ARQRedisSettings
        url = settings.redis_url or "redis://localhost:6379/0"
        # Parse redis://host:port/db
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return ARQRedisSettings(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            database=int(parsed.path.lstrip("/") or "0"),
            password=parsed.password,
        )

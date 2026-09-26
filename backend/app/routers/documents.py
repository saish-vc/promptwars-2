"""Document upload and paste endpoints.

Upload flow (production mode):
- Small files (≤ ``LARGE_FILE_THRESHOLD`` bytes / ≤ ``LARGE_PAGE_THRESHOLD`` pages):
  processed synchronously, ``200 OK`` with ``DocumentResponse`` (backward-compatible).
- Large files: stored in S3 and queued as an ARQ background job,
  ``202 Accepted`` with ``JobAcceptedResponse``.

Fallback mode (``ENABLE_FALLBACK_MODE=true``):
  All uploads are processed synchronously via the legacy SQLite DocumentStore.
"""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.documents import DocumentResponse, PasteDocumentRequest
from app.services.documents import (
    DocumentStore,
    extract_text,
    get_async_store,
    blob_storage,
)

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

# ── Backward-compatible legacy store (used only in fallback mode) ─────────────
store = DocumentStore(settings.database_path)

# Large-file thresholds that trigger async background processing
LARGE_FILE_THRESHOLD_BYTES = 2 * 1024 * 1024  # 2 MB
LARGE_PAGE_THRESHOLD = 5  # PDF pages


class JobAcceptedResponse(BaseModel):
    """Returned with HTTP 202 when a file is queued for background processing."""

    job_id: str
    doc_id: str
    status: str = "pending"
    message: str = "Document queued for processing. Poll /jobs/{job_id} for status."


# ── Paste endpoint ────────────────────────────────────────────────────────────


@router.post("/paste", response_model=DocumentResponse)
async def paste_document(payload: PasteDocumentRequest) -> DocumentResponse:
    """Accept plain-text document content and persist it."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document text is required",
        )
    safe_filename = os.path.basename(payload.filename) if payload.filename else "pasted_text.txt"

    if settings.enable_fallback_mode:
        doc_id = store.save(text, safe_filename)
    else:
        doc_id = await get_async_store().save(text, safe_filename)

    return DocumentResponse(doc_id=doc_id, text=text)


# ── Upload endpoint ───────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=DocumentResponse,
    responses={202: {"model": JobAcceptedResponse}},
)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF, DOCX, or TXT file.

    - Small files are processed synchronously and return ``DocumentResponse``.
    - Large files (>2 MB or >5 PDF pages) are queued as background jobs and
      return ``202 Accepted`` with a ``JobAcceptedResponse``.
    - In fallback/dev mode, all files are processed synchronously.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A filename is required",
        )
    safe_filename = os.path.basename(file.filename)
    content = await file.read(settings.max_upload_bytes + 1)

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large",
        )

    # ── Fallback / dev mode: synchronous processing ───────────────────────────
    if settings.enable_fallback_mode:
        try:
            text = await asyncio.to_thread(extract_text, safe_filename, content)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        doc_id = store.save(text, safe_filename)
        return DocumentResponse(doc_id=doc_id, text=text)

    # ── Production mode ───────────────────────────────────────────────────────
    is_large = len(content) > LARGE_FILE_THRESHOLD_BYTES or _is_large_pdf(
        safe_filename, content
    )

    if is_large:
        return await _enqueue_document(safe_filename, content)

    # Small file — process synchronously
    try:
        text = await asyncio.to_thread(extract_text, safe_filename, content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    doc_id = await get_async_store().save(text, safe_filename)
    return DocumentResponse(doc_id=doc_id, text=text)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _is_large_pdf(filename: str, content: bytes) -> bool:
    """Return True when the file is a PDF with more than LARGE_PAGE_THRESHOLD pages."""
    if not filename.lower().endswith(".pdf"):
        return False
    try:
        from io import BytesIO
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return len(reader.pages) > LARGE_PAGE_THRESHOLD
    except Exception:
        return False


async def _enqueue_document(filename: str, content: bytes) -> JobAcceptedResponse:
    """Upload raw bytes to S3 and dispatch an ARQ background processing job."""
    from app.db.base import get_session
    from app.db.models import AnalysisJob, Document

    doc_id = uuid4().hex
    job_id = uuid4().hex
    raw_key = f"documents/{doc_id}/raw/{filename}"

    # Store raw bytes in S3
    try:
        await blob_storage.upload(raw_key, content)
    except Exception as exc:
        logger.exception("Failed to upload raw file to S3: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store document — storage unavailable",
        ) from exc

    # Create Document + AnalysisJob rows
    async with get_session() as session:
        session.add(Document(doc_id=doc_id, filename=filename, s3_key=raw_key))
        session.add(AnalysisJob(job_id=job_id, doc_id=doc_id))

    # Enqueue ARQ job
    try:
        from arq import create_pool
        from app.worker import WorkerSettings

        redis_pool = await create_pool(WorkerSettings.redis_settings())
        await redis_pool.enqueue_job(
            "process_document_task",
            job_id=job_id,
            doc_id=doc_id,
            s3_key=raw_key,
            filename=filename,
        )
        await redis_pool.aclose()
    except Exception as exc:
        logger.exception("Failed to enqueue ARQ job: %s", exc)
        try:
            async with get_session() as session:
                document = await session.get(Document, doc_id)
                if document:
                    await session.delete(document)
            await blob_storage.delete(raw_key)
        except Exception:
            logger.exception("Failed to clean up unqueued document: doc_id=%s", doc_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to queue document processing job",
        ) from exc

    logger.info("Enqueued background job: job_id=%s doc_id=%s", job_id, doc_id)
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=JobAcceptedResponse(job_id=job_id, doc_id=doc_id).model_dump(),
    )

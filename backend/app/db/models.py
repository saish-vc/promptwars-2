"""SQLAlchemy ORM models for LegiFlow.

Tables:
- ``documents``       — document metadata and S3 object key
- ``document_chunks`` — text chunks with optional pgvector embeddings
- ``analysis_jobs``   — background task job tracking
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector

    _VECTOR_AVAILABLE = True
except ImportError:
    _VECTOR_AVAILABLE = False
    Vector = None  # type: ignore[assignment,misc]


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ── Document ──────────────────────────────────────────────────────────────────


class Document(Base):
    """Persisted document metadata.

    Attributes:
        doc_id:       UUID hex string (primary key, returned to clients).
        filename:     Original uploaded filename.
        s3_key:       Object key in S3/MinIO bucket (nullable if fallback mode).
        text_preview: First 500 characters of extracted text for quick display.
        text:         Full extracted text (stored in DB in fallback mode; nullable
                      when S3 is active and text is stored as a blob).
        created_at:   Timestamp of creation.
    """

    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    text_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Full text stored here only in fallback/SQLite mode
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    jobs: Mapped[list[AnalysisJob]] = relationship(
        "AnalysisJob", back_populates="document", cascade="all, delete-orphan"
    )


# ── Document Chunk ────────────────────────────────────────────────────────────


class DocumentChunk(Base):
    """A text chunk of a document, with an optional embedding vector.

    Embeddings are stored as a pgvector ``Vector`` column when the extension is
    available, otherwise stored as ``Text`` (JSON-serialised list of floats) for
    SQLite compatibility.

    Attributes:
        id:          Auto-increment primary key.
        doc_id:      FK to ``documents.doc_id``.
        chunk_index: Zero-based position of the chunk in the document.
        text:        Raw chunk text.
        embedding:   Dense embedding vector (pgvector) or None.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # pgvector column — nullable so chunks work without embedding enabled
    if _VECTOR_AVAILABLE and Vector is not None:
        embedding: Mapped[list[float] | None] = mapped_column(
            Vector(1024), nullable=True
        )
    else:
        # SQLite / no-pgvector fallback: store serialised JSON text
        embedding: Mapped[str | None] = mapped_column(Text, nullable=True)  # type: ignore[assignment]

    document: Mapped[Document] = relationship("Document", back_populates="chunks")


# ── Analysis Job ──────────────────────────────────────────────────────────────


class JobStatus(str, enum.Enum):
    """Background analysis job lifecycle states."""

    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class AnalysisJob(Base):
    """Tracks the status of an async background document processing job.

    Attributes:
        job_id:      UUID hex string (returned in 202 response).
        doc_id:      FK to ``documents.doc_id``.
        status:      Current job lifecycle state.
        result_json: JSON-serialised result payload when status=done.
        error:       Error message when status=failed.
        created_at:  Job creation timestamp.
        updated_at:  Last status update timestamp.
    """

    __tablename__ = "analysis_jobs"

    job_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    doc_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.pending, nullable=False
    )
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    document: Mapped[Document] = relationship("Document", back_populates="jobs")

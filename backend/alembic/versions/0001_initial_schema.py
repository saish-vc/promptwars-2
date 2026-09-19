"""Initial schema — documents, document_chunks, analysis_jobs.

Revision ID: 0001
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── documents ─────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("doc_id", sa.String(32), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=True),
        sa.Column("s3_key", sa.String(1024), nullable=True),
        sa.Column("text_preview", sa.String(500), nullable=True),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── document_chunks ───────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "doc_id",
            sa.String(32),
            sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        # pgvector column — 1024-dim
        sa.Column(
            "embedding",
            sa.Text,  # placeholder; actual Vector type set via raw SQL below
            nullable=True,
        ),
    )
    # Convert embedding column to native vector type
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024) USING NULL::vector(1024)")
    # Create approximate nearest-neighbour index (IVFFlat)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunks_embedding "
        "ON document_chunks USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )
    op.create_index("ix_chunks_doc_id", "document_chunks", ["doc_id"])

    # ── analysis_jobs ─────────────────────────────────────────
    op.create_table(
        "analysis_jobs",
        sa.Column("job_id", sa.String(32), primary_key=True),
        sa.Column(
            "doc_id",
            sa.String(32),
            sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "done", "failed", name="jobstatus"),
            default="pending",
            nullable=False,
        ),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("error", sa.String(2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_jobs_doc_id", "analysis_jobs", ["doc_id"])
    op.create_index("ix_jobs_status", "analysis_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("analysis_jobs")
    op.drop_index("ix_chunks_embedding", table_name="document_chunks")
    op.drop_index("ix_chunks_doc_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP TYPE IF EXISTS jobstatus")

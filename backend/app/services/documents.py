import logging
import sqlite3
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DocumentStore:
    def __init__(self, path: str):
        self.path = path

    def initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS documents (doc_id TEXT PRIMARY KEY, filename TEXT, text TEXT NOT NULL)"
            )

    def save(self, text: str, filename: str | None = None) -> str:
        doc_id = uuid4().hex
        with sqlite3.connect(self.path) as connection:
            connection.execute("INSERT INTO documents VALUES (?, ?, ?)", (doc_id, filename, text))
        return doc_id

    def get_text(self, doc_id: str) -> str | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT text FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        return row[0] if row else None


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt"}


def _first_line(content: bytes) -> str:
    """Best-effort first non-empty line for debugging extraction failures."""
    try:
        text = content.decode("utf-8-sig", errors="replace")
    except Exception:
        text = ""
    for line in text.splitlines():
        if line.strip():
            return line[:200]
    return ""


def extract_text(filename: str, content: bytes) -> str:
    filename = str(filename).strip() or "unknown"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError("Only PDF, DOCX, and TXT files are supported")
    try:
        if suffix == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        elif suffix == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs)
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

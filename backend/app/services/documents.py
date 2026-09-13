import sqlite3
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader


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


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        elif suffix == ".docx":
            text = "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs)
        elif suffix == ".txt":
            text = content.decode("utf-8-sig")
        else:
            raise ValueError("Only PDF, DOCX, and TXT files are supported")
    except Exception as exc:
        raise ValueError("Could not extract text from this file") from exc
    if not text.strip():
        raise ValueError("This document contains no extractable text")
    return text.strip()

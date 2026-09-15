import os
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.schemas.documents import DocumentResponse, PasteDocumentRequest
from app.services.documents import DocumentStore, extract_text

router = APIRouter(prefix="/documents", tags=["documents"])
store = DocumentStore(settings.database_path)


@router.post("/paste", response_model=DocumentResponse)
async def paste_document(payload: PasteDocumentRequest) -> DocumentResponse:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document text is required")
    safe_filename = os.path.basename(payload.filename) if payload.filename else "pasted_text.txt"
    return DocumentResponse(doc_id=store.save(text, safe_filename), text=text)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A filename is required")
    safe_filename = os.path.basename(file.filename)
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")
    try:
        text = extract_text(safe_filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return DocumentResponse(doc_id=store.save(text, safe_filename), text=text)

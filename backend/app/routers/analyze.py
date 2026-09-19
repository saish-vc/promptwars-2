from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.routers.documents import store
from app.schemas.analysis import AnalysisResponse
from app.services.analysis import analyze_document
from app.services.documents import get_async_store

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    text: str | None = Field(default=None, description="Raw document text")
    doc_id: str | None = Field(default=None, description="Persisted document ID")


async def _resolve_document_text(payload: AnalyzeRequest) -> str:
    if payload.text and payload.text.strip():
        return payload.text.strip()
    if payload.doc_id:
        if settings.enable_fallback_mode:
            text = store.get_text(payload.doc_id)
        else:
            text = await get_async_store().get_text(payload.doc_id)
        if text and text.strip():
            return text.strip()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with doc_id '{payload.doc_id}' not found",
        )
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Either 'text' or 'doc_id' must be provided",
    )


@router.post("/document", response_model=AnalysisResponse)
@router.post("/contract", response_model=AnalysisResponse)
async def analyze_document_endpoint(payload: AnalyzeRequest) -> AnalysisResponse:
    text = await _resolve_document_text(payload)
    try:
        return await analyze_document(text)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

from fastapi import APIRouter, HTTPException, status

from app.routers.documents import store
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import chat_about_contract, MalformedRAGError
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])


def _resolve_text(doc_id: str) -> str | None:
    """Sync text resolver — used in fallback mode only."""
    if settings.enable_fallback_mode:
        return store.get_text(doc_id)
    return None  # async store will be used inside RAGService


@router.post("", response_model=ChatResponse)
@router.post("/contract", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Question is required")
    try:
        return await chat_about_contract(payload, _resolve_text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MalformedRAGError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Chat generation failed after retry")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.routers.documents import store
from app.schemas.negotiation import NegotiationRequest, NegotiationResponse
from app.services.documents import get_async_store
from app.services.negotiation import generate_negotiation

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/negotiation", response_model=NegotiationResponse)
async def generate_negotiation_endpoint(payload: NegotiationRequest) -> NegotiationResponse:
    text = payload.text.strip() if payload.text else ""
    if not text and payload.doc_id:
        if settings.enable_fallback_mode:
            text = store.get_text(payload.doc_id) or ""
        else:
            text = (await get_async_store().get_text(payload.doc_id)) or ""
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document text or valid doc_id is required",
        )

    title = payload.clause_title or payload.clause_topic or "High Risk Clause"
    clause_text = payload.clause_text or title
    analysis = payload.analysis or {"summary": text[:200], "risks": [title]}
    user_role = payload.user_role or "Buyer"

    req = NegotiationRequest(
        text=text,
        doc_id=payload.doc_id,
        analysis=analysis,
        clause_title=title,
        clause_topic=payload.clause_topic,
        clause_text=clause_text,
        user_role=user_role,
    )

    try:
        return await generate_negotiation(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
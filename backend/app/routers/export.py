from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.routers.documents import store
from app.schemas.export import LawyerPackRequest, LawyerPackResponse
from app.services.export import generate_lawyer_pack

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/lawyer-pack", response_class=PlainTextResponse)
async def export_lawyer_pack(payload: LawyerPackRequest) -> str:
    if not payload.analysis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Analysis data is required to generate a lawyer pack",
        )
    doc_text = store.get_text(payload.doc_id)
    if not doc_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    result = generate_lawyer_pack(payload, store)
    return result.content

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.schemas.analysis import AnalysisResponse
from app.services.analysis import analyze_document

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    text: str


@router.post("/document", response_model=AnalysisResponse)
async def analyze_document_endpoint(payload: AnalyzeRequest) -> AnalysisResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document text is required")
    try:
        return await analyze_document(payload.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

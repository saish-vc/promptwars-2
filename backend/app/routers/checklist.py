from fastapi import APIRouter, HTTPException, status

from app.schemas.checklist import ChecklistRequest, ChecklistResponse
from app.services.checklist import generate_checklist, MalformedChecklistError

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/checklist", response_model=ChecklistResponse)
async def generate_checklist_endpoint(payload: ChecklistRequest) -> ChecklistResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document text is required")
    try:
        return await generate_checklist(payload)
    except MalformedChecklistError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Checklist generation failed after retry")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
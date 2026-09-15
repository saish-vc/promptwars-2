from fastapi import APIRouter, HTTPException, status

from app.schemas.negotiation import NegotiationRequest, NegotiationResponse
from app.services.negotiation import generate_negotiation, MalformedNegotiationError

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/negotiation", response_model=NegotiationResponse)
async def generate_negotiation_endpoint(payload: NegotiationRequest) -> NegotiationResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Document text is required")
    try:
        return await generate_negotiation(payload)
    except MalformedNegotiationError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Negotiation generation failed after retry")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
from fastapi import APIRouter, HTTPException, status

from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.services.comparison import compare_contracts
from app.routers.documents import store

router = APIRouter(prefix="/compare", tags=["compare"])


def _resolve_text(doc_id: str) -> str | None:
    return store.get_text(doc_id)


@router.post("/contracts", response_model=ComparisonResponse)
async def compare_contracts_endpoint(payload: ComparisonRequest) -> ComparisonResponse:
    try:
        return await compare_contracts(payload, _resolve_text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

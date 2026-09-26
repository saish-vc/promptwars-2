import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.core.config import settings
from app.db.base import get_session
from app.dependencies import get_redis_client
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        if not settings.enable_fallback_mode:
            redis = await get_redis_client()
            if redis is None:
                raise RuntimeError("Redis is unavailable")
            await redis.ping()
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies are unavailable",
        ) from exc
    return HealthResponse(status="ok")

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.health import router as health_router
from app.routers.documents import router as documents_router
from app.routers.documents import store as document_store
from app.routers.analyze import router as analyze_router
from app.routers.compare import router as compare_router
from app.routers.checklist import router as checklist_router
from app.routers.negotiation import router as negotiation_router
from app.routers.chat import router as chat_router
from app.routers.export import router as export_router
from app.routers.jobs import router as jobs_router

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application startup and shutdown lifecycle manager.

    Startup sequence:
    1. Initialise PostgreSQL / SQLite async engine and create tables.
    2. Initialise Redis connection pool.
    3. Ensure S3/MinIO bucket exists (if configured).
    4. Initialise legacy DocumentStore (SQLite shim, fallback mode only).

    Shutdown sequence (reverse order):
    1. Close Redis pool.
    2. Dispose SQLAlchemy engine.
    """
    # ── 1. Database ───────────────────────────────────────────
    missing = settings.production_errors()
    if missing:
        raise RuntimeError("Production configuration is missing: " + ", ".join(missing))

    try:
        from app.db.base import create_all_tables, dispose_engine

        await create_all_tables()
    except Exception as exc:
        logger.error("Database initialisation failed: %s", exc)
        raise

    # ── 2. Redis ──────────────────────────────────────────────
    from app.dependencies import init_redis, close_redis

    await init_redis()

    # ── 3. S3 / MinIO bucket ──────────────────────────────────
    if settings.s3_configured:
        try:
            from app.services.documents import blob_storage, S3BlobStorage

            if isinstance(blob_storage, S3BlobStorage):
                async with blob_storage._client() as client:
                    await blob_storage._ensure_bucket(client)
                logger.info("S3 bucket '%s' ready", settings.s3_bucket_name)
        except Exception as exc:
            logger.warning("S3 bucket init failed (non-fatal): %s", exc)

    # ── 4. Legacy SQLite shim (fallback mode) ─────────────────
    if settings.enable_fallback_mode:
        document_store.initialize()

    logger.info(
        "LegiFlow started | provider=%s | fallback=%s | redis=%s | s3=%s | embeddings=%s",
        settings.llm_provider,
        settings.enable_fallback_mode,
        settings.redis_configured,
        settings.s3_configured,
        settings.embedding_active,
    )

    yield  # ── Application running ──────────────────────────

    # ── Shutdown ──────────────────────────────────────────────
    await close_redis()
    await dispose_engine()
    logger.info("LegiFlow shutdown complete")


app = FastAPI(title="LegiFlow", lifespan=lifespan)

# ── Security Headers Middleware ───────────────────────────────────────────────


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000;"
    )
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(analyze_router)
app.include_router(compare_router)
app.include_router(checklist_router)
app.include_router(negotiation_router)
app.include_router(chat_router)
app.include_router(export_router)
app.include_router(jobs_router)  # NEW: background job status polling


# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid request", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    # Surface clean 503 for circuit breaker errors
    from app.services.llm import CircuitOpenError

    if isinstance(exc, CircuitOpenError):
        logger.warning("Circuit breaker rejected request: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "LLM service temporarily unavailable. Please retry in a moment."},
        )
    logger.exception("Unhandled request error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

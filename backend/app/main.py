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

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    document_store.initialize()
    yield


app = FastAPI(title="LegiFlow", lifespan=lifespan)

# Security Headers Middleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(analyze_router)
app.include_router(compare_router)
app.include_router(checklist_router)
app.include_router(negotiation_router)
app.include_router(chat_router)
app.include_router(export_router)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid request", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

import logging
import os


logger = logging.getLogger(__name__)


class Settings:
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    cors_origins = [origin for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin]
    nim_api_key = os.getenv("NIM_API_KEY", "")
    nim_base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    database_path = os.getenv("DATABASE_PATH", "/tmp/legiflow.db")
    max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", "10485760"))


settings = Settings()


if not settings.nim_api_key:
    logger.warning("NIM_API_KEY is not set; LLM paths will fail at runtime")
else:
    logger.info("NIM_API_KEY is configured")

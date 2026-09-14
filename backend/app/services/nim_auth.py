from typing import Dict

from app.core.config import settings


def build_nim_auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.nim_api_key}",
        "Content-Type": "application/json",
    }

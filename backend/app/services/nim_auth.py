import time
import base64
import hmac
import hashlib
import json
from typing import Dict, Any

from app.core.config import settings


NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_METHOD = "POST"


def _sign_message(secret: str, message: str) -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()


def build_nim_credential() -> Dict[str, Any]:
    now = int(time.time())
    iss = settings.nim_api_key
    header = {
        "alg": "HS256",
        "typ": "JWT",
        "kid": iss,
    }
    payload = {
        "iss": iss,
        "sub": "vapi",
        "aud": NIM_URL,
        "iat": now,
        "exp": now + 1200,
        "nbf": now,
    }
    header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}"
    signature = _sign_message(iss, signing_input)
    return {
        "scheme": "APIKey",
        "key": iss,
        "sig": signature,
        "ts": now,
    }


def build_nim_auth_headers() -> Dict[str, Any]:
    cred = build_nim_credential()
    return {
        "Authorization": json.dumps(cred),
        "Content-Type": "application/json",
    }

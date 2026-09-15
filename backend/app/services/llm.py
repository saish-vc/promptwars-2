from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import logging

import httpx

from app.core.config import settings
from app.services.nim_auth import build_nim_auth_headers

logger = logging.getLogger(__name__)

LEGAL_DISCLAIMER = (
    "You provide general legal information, not legal advice. Do not interpret local laws "
    "beyond the provided text. Encourage the user to consult a qualified lawyer."
)

NIM_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"

GROQ_MODEL = settings.groq_model or "openai/gpt-oss-20b"

GENERATION_CONFIG = {
    "temperature": 0.2,
    "max_tokens": 2048,
    "top_p": 1.0,
    "stream": False,
}

PROVIDER_NIM = "nim"
PROVIDER_GROQ = "groq"


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> str: ...


class NIMClient(LLMClient):
    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(base_url=settings.nim_base_url, timeout=120.0)
        return self._http

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        if not settings.nim_api_key:
            raise RuntimeError("NIM_API_KEY is not configured")

        http = await self._http_client()
        headers = build_nim_auth_headers()

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await http.post(
                    "/chat/completions",
                    json={
                        "model": NIM_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        **GENERATION_CONFIG,
                    },
                    headers=headers,
                )
            except httpx.RequestError as exc:
                logger.warning("NIM request failed, will retry: %s", exc)
                if attempt >= 2:
                    raise RuntimeError("NIM request failed") from exc
                await asyncio.sleep(1)
                continue

            if response.status_code == 429:
                logger.warning("NIM returned 429, will retry once")
                if attempt >= 2:
                    response.raise_for_status()
                await asyncio.sleep(1)
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "NIM returned %s for %s",
                    response.status_code,
                    response.url,
                    extra={"status_code": response.status_code, "body_preview": response.text[:500]},
                )
                raise RuntimeError(f"NIM error {response.status_code}") from exc
            body = response.json()
            choices = body.get("choices") or []
            if not choices:
                raise RuntimeError("NIM returned an empty response")
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if not content.strip():
                raise RuntimeError("NIM returned an empty completion")
            return content


class GroqClient(LLMClient):
    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url="https://api.groq.com/openai/v1",
                timeout=120.0,
            )
        return self._http

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        http = await self._http_client()
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        attempt = 0
        while True:
            attempt += 1
            try:
                response = await http.post(
                    "/chat/completions",
                    json={
                        "model": GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        **GENERATION_CONFIG,
                    },
                    headers=headers,
                )
            except httpx.RequestError as exc:
                logger.warning("Groq request failed, will retry: %s", exc)
                if attempt >= 2:
                    raise RuntimeError("Groq request failed") from exc
                await asyncio.sleep(1)
                continue

            if response.status_code == 429:
                logger.warning("Groq returned 429, will retry once")
                if attempt >= 2:
                    response.raise_for_status()
                await asyncio.sleep(1)
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Groq returned %s for %s",
                    response.status_code,
                    response.url,
                    extra={"status_code": response.status_code, "body_preview": response.text[:500]},
                )
                raise RuntimeError(f"Groq error {response.status_code}") from exc
            body = response.json()
            choices = body.get("choices") or []
            if not choices:
                raise RuntimeError("Groq returned an empty response")
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if not content.strip():
                raise RuntimeError("Groq returned an empty completion")
            return content


def build_llm_client() -> LLMClient:
    provider = (settings.llm_provider or "").lower()
    if provider == PROVIDER_GROQ:
        logger.info("Using Groq LLM client (model=%s)", GROQ_MODEL)
        return GroqClient()
    logger.info("Using NIM LLM client (model=%s)", NIM_MODEL)
    return NIMClient()


llm_client: LLMClient = build_llm_client()

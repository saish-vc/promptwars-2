"""LLM client abstraction with Redis caching, tenacity retries, and circuit breaking.

Provider support:
- **NIM**  (``nvidia/llama-3.1-nemotron-70b-instruct``)
- **Groq** (configurable model)

Resilience features:
- **Redis prompt cache**: SHA-256 keyed, configurable TTL (default 24 h).
  Falls back to direct API calls when Redis is unavailable.
- **Tenacity retries**: exponential backoff with jitter for transient errors
  and HTTP 429/503 responses.
- **Circuit breaker**: after 5 consecutive failures within 60 s, the circuit
  opens and subsequent calls raise ``CircuitOpenError`` immediately, giving
  the provider time to recover without hammering a down endpoint.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.core.config import settings
from app.services.nim_auth import build_nim_auth_headers

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

LEGAL_DISCLAIMER = (
    "You provide general legal information, not legal advice. Do not interpret local laws "
    "beyond the provided text. Encourage the user to consult a qualified lawyer."
)

NIM_MODEL = settings.nim_model or "meta/llama-3.2-11b-vision-instruct"
GROQ_MODEL = settings.groq_model or "openai/gpt-oss-120b"

GENERATION_CONFIG = {
    "temperature": 0.2,
    "max_tokens": 2048,
    "top_p": 1.0,
    "stream": False,
}

PROVIDER_NIM = "nim"
PROVIDER_GROQ = "groq"

# Circuit breaker config
_CB_FAILURE_THRESHOLD = 5   # consecutive failures to open the circuit
_CB_WINDOW_SECONDS = 60     # rolling window for failure count
_CB_OPEN_DURATION = 30      # seconds the circuit stays open


# ── Exceptions ────────────────────────────────────────────────────────────────


class RateLimitError(RuntimeError):
    """Raised on HTTP 429 responses — signals tenacity to retry."""


class ServiceUnavailableError(RuntimeError):
    """Raised on HTTP 503 responses — signals tenacity to retry."""


class CircuitOpenError(RuntimeError):
    """Raised when the circuit breaker is open and calls are rejected."""


# ── Redis prompt cache ────────────────────────────────────────────────────────


class PromptCache:
    """Redis-backed cache for LLM completions.

    Cache key: ``llm:<sha256(provider|model|system_prompt|prompt|config)>``
    """

    def _key(self, provider: str, model: str, system_prompt: str, prompt: str) -> str:
        payload = json.dumps(
            {
                "provider": provider,
                "model": model,
                "system": system_prompt,
                "prompt": prompt,
                **GENERATION_CONFIG,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return f"llm:{digest}"

    async def get(self, provider: str, model: str, system_prompt: str, prompt: str) -> str | None:
        if not settings.redis_configured:
            return None
        try:
            from app.dependencies import get_redis_client

            redis = await get_redis_client()
            raw = await redis.get(self._key(provider, model, system_prompt, prompt))
            if raw:
                logger.debug("LLM cache hit")
                return raw.decode() if isinstance(raw, bytes) else raw
        except Exception as exc:
            logger.debug("PromptCache.get failed: %s", exc)
        return None

    async def set(self, provider: str, model: str, system_prompt: str, prompt: str, content: str) -> None:
        if not settings.redis_configured:
            return
        try:
            from app.dependencies import get_redis_client

            redis = await get_redis_client()
            await redis.set(
                self._key(provider, model, system_prompt, prompt),
                content,
                ex=settings.cache_ttl_seconds,
            )
        except Exception as exc:
            logger.debug("PromptCache.set failed: %s", exc)


prompt_cache = PromptCache()


# ── Circuit breaker ────────────────────────────────────────────────────────────


class CircuitBreaker:
    """In-process circuit breaker tracking consecutive LLM failures.

    State machine: CLOSED → (threshold failures) → OPEN → (cooldown) → CLOSED.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._failures: list[float] = []  # timestamps of recent failures
        self._open_until: float = 0.0

    def is_open(self) -> bool:
        now = time.monotonic()
        if now < self._open_until:
            return True
        # Prune stale failure timestamps outside the window
        self._failures = [t for t in self._failures if now - t <= _CB_WINDOW_SECONDS]
        return False

    def record_failure(self) -> None:
        now = time.monotonic()
        self._failures.append(now)
        self._failures = [t for t in self._failures if now - t <= _CB_WINDOW_SECONDS]
        if len(self._failures) >= _CB_FAILURE_THRESHOLD:
            self._open_until = now + _CB_OPEN_DURATION
            logger.warning(
                "Circuit breaker OPEN for provider=%s (cooldown=%ds)",
                self._name,
                _CB_OPEN_DURATION,
            )

    def record_success(self) -> None:
        self._failures.clear()
        self._open_until = 0.0


# ── Retry predicate ───────────────────────────────────────────────────────────


def _is_retryable(exc: BaseException) -> bool:
    """Return True for transient errors that should trigger a tenacity retry."""
    return isinstance(exc, (httpx.RequestError, RateLimitError, ServiceUnavailableError))


def _tenacity_retry(**extra):
    return retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=30) + wait_random(0, 2),
        reraise=True,
        **extra,
    )


# ── LLM client interface ──────────────────────────────────────────────────────


class LLMClient(ABC):
    provider: str = ""
    model: str = ""
    _cb: CircuitBreaker

    @abstractmethod
    async def _call_api(self, prompt: str, system_prompt: str) -> str: ...

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """Return an LLM completion, using Redis cache and circuit breaker.

        Args:
            prompt:        User/content prompt.
            system_prompt: System instruction (optional).

        Returns:
            The LLM-generated text content.

        Raises:
            CircuitOpenError: When the circuit breaker is open.
            RuntimeError:     On persistent API failure after retries.
        """
        if self._cb.is_open():
            raise CircuitOpenError(
                f"LLM provider '{self.provider}' circuit breaker is open — "
                "too many recent failures. Retry after a short wait."
            )

        # Check Redis cache
        cached = await prompt_cache.get(self.provider, self.model, system_prompt, prompt)
        if cached:
            return cached

        try:
            content = await self._call_api(prompt, system_prompt)
        except Exception:
            self._cb.record_failure()
            raise

        self._cb.record_success()
        await prompt_cache.set(self.provider, self.model, system_prompt, prompt, content)
        return content


# ── NIM client ────────────────────────────────────────────────────────────────


class NIMClient(LLMClient):
    provider = PROVIDER_NIM
    model = NIM_MODEL

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._cb = CircuitBreaker(self.provider)

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            base_url = settings.nim_base_url.rstrip("/") + "/"
            self._http = httpx.AsyncClient(base_url=base_url, timeout=120.0)
        return self._http

    @_tenacity_retry()
    async def _call_api(self, prompt: str, system_prompt: str) -> str:
        if not settings.nim_api_key:
            raise RuntimeError("NIM_API_KEY is not configured")

        http = await self._http_client()
        headers = build_nim_auth_headers()

        response = await http.post(
            "chat/completions",
            json={
                "model": settings.nim_model or NIM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                **GENERATION_CONFIG,
            },
            headers=headers,
        )

        if response.status_code == 429:
            logger.warning("NIM returned 429 — backing off (tenacity will retry)")
            raise RateLimitError("NIM rate limit exceeded")
        if response.status_code == 503:
            raise ServiceUnavailableError("NIM service unavailable")

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


# ── Groq client ───────────────────────────────────────────────────────────────


class GroqClient(LLMClient):
    provider = PROVIDER_GROQ
    model = GROQ_MODEL

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._cb = CircuitBreaker(self.provider)

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url="https://api.groq.com/openai/v1", timeout=120.0
            )
        return self._http

    @_tenacity_retry()
    async def _call_api(self, prompt: str, system_prompt: str) -> str:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        http = await self._http_client()
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

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

        if response.status_code == 429:
            logger.warning("Groq returned 429 — backing off (tenacity will retry)")
            raise RateLimitError("Groq rate limit exceeded")
        if response.status_code == 503:
            raise ServiceUnavailableError("Groq service unavailable")

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


# ── Factory & singleton ───────────────────────────────────────────────────────


def build_llm_client() -> LLMClient:
    provider = (settings.llm_provider or "").lower()
    if provider == PROVIDER_GROQ:
        logger.info("Using Groq LLM client (model=%s)", GROQ_MODEL)
        return GroqClient()
    logger.info("Using NIM LLM client (model=%s)", NIM_MODEL)
    return NIMClient()


llm_client: LLMClient = build_llm_client()

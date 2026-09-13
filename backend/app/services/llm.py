from abc import ABC, abstractmethod

from app.core.config import settings

LEGAL_DISCLAIMER = (
    "You provide general legal information, not legal advice. Do not interpret local laws "
    "beyond the provided text. Encourage the user to consult a qualified lawyer."
)


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> str: ...


class NIMClient(LLMClient):
    """Stage 1 placeholder; later stages add the NIM SDK call here only."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        if not settings.nim_api_key:
            raise RuntimeError("NIM_API_KEY is not configured")
        raise NotImplementedError("NIM integration is added in Stage 3")


llm_client: LLMClient = NIMClient()

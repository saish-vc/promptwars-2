import logging
from abc import ABC, abstractmethod

from app.schemas.checklist import ChecklistItem, ChecklistRequest, ChecklistResponse, LawyerQuestion
from app.services.llm import LEGAL_DISCLAIMER, llm_client

logger = logging.getLogger(__name__)

CHECKLIST_SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "You are generating a checklist and lawyer questions based on contract analysis. "
    + "Return ONLY a single JSON object with these exact keys: "
    + "`checklist` and `lawyer_questions`.\n\n"
    + "`checklist`: a list of objects, each with `item` (the checklist item text) "
    + "and `status` (default to 'pending').\n\n"
    + "`lawyer_questions`: a list of objects, each with `question` (the question to ask a lawyer) "
    + "and `context` (which clause or risk this relates to).\n\n"
    + "Base the checklist and questions on the provided contract text and analysis. "
    + "Focus on actionable items and important legal considerations. "
    + "Be specific to the contract content, not generic boilerplate."
)

CHECKLIST_PROMPT_PARTIAL = (
    "Contract text:\n\n{text}\n\n"
    "Analysis:\n\n{analysis}\n"
)


class ChecklistService(ABC):
    @abstractmethod
    async def generate(self, request: ChecklistRequest) -> ChecklistResponse: ...


class NIMChecklistService(ChecklistService):
    async def generate(self, request: ChecklistRequest) -> ChecklistResponse:
        prompt = CHECKLIST_SYSTEM_PROMPT + "\n\n" + CHECKLIST_PROMPT_PARTIAL.format(
            text=request.text, analysis=str(request.analysis)
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw)

    def _parse(self, raw: str) -> ChecklistResponse:
        from app.services.analysis import _first_json_object, _clean_json_candidate

        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedChecklistError("No JSON object found in the LLM response")
        try:
            parsed = ChecklistResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedChecklistError("LLM response did not match the expected checklist schema") from exc
        return parsed


class MalformedChecklistError(RuntimeError):
    pass


async def generate_checklist(
    request: ChecklistRequest,
    service: ChecklistService | None = None,
) -> ChecklistResponse:
    service = service or NIMChecklistService()
    try:
        return await service.generate(request)
    except MalformedChecklistError:
        logger.warning("First checklist generation failed, retrying once")
        try:
            return await service.generate(request)
        except MalformedChecklistError as exc:
            logger.error("Checklist generation retry failed: %s", exc)
            raise RuntimeError("Checklist generation failed after retry") from exc
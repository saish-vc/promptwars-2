import logging

from app.schemas.negotiation import NegotiationRequest, NegotiationResponse
from app.services.llm import LEGAL_DISCLAIMER, llm_client
from app.services.analysis import _clean_json_candidate, _first_json_object

logger = logging.getLogger(__name__)

NEGOTIATION_SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "You are generating negotiation suggestions for a specific contract clause. "
    + "Return ONLY a single JSON object with these exact keys: "
    + "`counter_clause` and `talking_points`.\n\n"
    + "`counter_clause`: the suggested replacement clause text that would be more favorable "
    + "to the user_role party.\n\n"
    + "`talking_points`: a list of 3-5 talking points the user can use in negotiation "
    + "to advocate for this change.\n\n"
    + "The counter_clause should be legally sound and realistic. "
    + "The talking points should be specific to the clause content and the user_role. "
    + "Do not use generic boilerplate."
)

NEGOTIATION_PROMPT_PARTIAL = (
    "user_role: {user_role}\n\n"
    "Contract text:\n\n{text}\n\n"
    "Analysis:\n\n{analysis}\n\n"
    "Risky clause title: {clause_title}\n"
    "Risky clause text: {clause_text}\n"
)


class MalformedNegotiationError(RuntimeError):
    pass


class NegotiationService:
    async def generate(self, request: NegotiationRequest) -> NegotiationResponse:
        prompt = NEGOTIATION_SYSTEM_PROMPT + "\n\n" + NEGOTIATION_PROMPT_PARTIAL.format(
            user_role=request.user_role,
            text=request.text,
            analysis=str(request.analysis),
            clause_title=request.clause_title,
            clause_text=request.clause_text,
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw)

    def _parse(self, raw: str) -> NegotiationResponse:
        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedNegotiationError("No JSON object found in the LLM response")
        try:
            parsed = NegotiationResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedNegotiationError("LLM response did not match the expected negotiation schema") from exc
        return parsed


async def generate_negotiation(
    request: NegotiationRequest,
    service: NegotiationService | None = None,
) -> NegotiationResponse:
    service = service or NegotiationService()
    try:
        return await service.generate(request)
    except MalformedNegotiationError:
        logger.warning("First negotiation generation failed, retrying once")
        try:
            return await service.generate(request)
        except MalformedNegotiationError as exc:
            logger.error("Negotiation generation retry failed: %s", exc)
            raise RuntimeError("Negotiation generation failed after retry") from exc
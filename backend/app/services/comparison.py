import logging

from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.services.llm import LEGAL_DISCLAIMER, llm_client
from app.services.analysis import _clean_json_candidate, _first_json_object

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "You are comparing two versions of a legal contract, labelled A and B. "
    + "Return ONLY a single JSON object with these exact keys: "
    + "`summary` and `differences`.\n\n"
    + "`summary`: one concise paragraph describing the overall nature of the changes.\n\n"
    + "`differences`: a list of objects, each describing ONE clause-level difference "
    + "between the two texts. Each object must have these exact keys:\n"
    + "  - `clause`: a short label for the clause (e.g. 'Payment terms').\n"
    + "  - `in_a`: the relevant text from version A (a short quote or paraphrase).\n"
    + "  - `in_b`: the relevant text from version B (a short quote or paraphrase).\n"
    + "  - `favors`: which party this clause favors — exactly one of "
    + "`seller`, `buyer`, or `neutral`.\n"
    + "  - `reason`: one line explaining why this clause favors that party.\n"
    + "  - `context_for_role`: why this difference matters specifically to the "
    + "`user_role` party, in one line.\n\n"
    + "Compare only clauses that actually differ between the two texts. "
    + "Do not invent differences that are not present. "
    + "If the two texts are identical in a section, skip it. "
    + "Label version A and version B in your quotes so it is clear which text each comes from.\n\n"
    + "The user_role is the party the user represents. "
    + "The `favors` field should be judged relative to the clause text itself, "
    + "not biased by user_role — user_role only affects `context_for_role`."
)

COMPARE_PROMPT_PARTIAL = (
    "user_role: {role}\n\n"
    "Version A:\n\n{a}\n\n"
    "Version B:\n\n{b}\n"
)


class MalformedComparisonError(RuntimeError):
    pass


class ComparisonService:
    async def compare(self, request: ComparisonRequest, resolve_text) -> ComparisonResponse:
        text_a = request.document_a.resolve(resolve_text)
        text_b = request.document_b.resolve(resolve_text)
        prompt = SYSTEM_PROMPT + "\n\n" + COMPARE_PROMPT_PARTIAL.format(
            role=request.user_role, a=text_a, b=text_b
        )
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw)

    def _parse(self, raw: str) -> ComparisonResponse:
        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedComparisonError("No JSON object found in the LLM response")
        try:
            parsed = ComparisonResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedComparisonError("LLM response did not match the expected comparison schema") from exc
        for diff in parsed.differences:
            if diff.favors not in {"seller", "buyer", "neutral"}:
                diff.favors = "neutral"
        return parsed


async def compare_contracts(
    request: ComparisonRequest,
    resolve_text,
    service: ComparisonService | None = None,
) -> ComparisonResponse:
    service = service or ComparisonService()
    try:
        return await service.compare(request, resolve_text)
    except MalformedComparisonError:
        logger.warning("First comparison parse failed, retrying once")
        try:
            return await service.compare(request, resolve_text)
        except MalformedComparisonError as exc:
            logger.error("Comparison retry failed: %s", exc)
            raise RuntimeError("Comparison failed after retry") from exc

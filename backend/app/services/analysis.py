import logging

from app.schemas.analysis import AnalysisResponse, RiskClause
from app.services.llm import LEGAL_DISCLAIMER, llm_client
from app.services.json_utils import clean_llm_json, safe_parse_json

logger = logging.getLogger(__name__)

# Keep old aliases for any code that imported them directly
_clean_json_candidate = clean_llm_json
_first_json_object = None  # No longer needed — use clean_llm_json directly


ANALYSIS_SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "Extract the following from the contract text below and return ONLY a single JSON object with these exact keys: "
    + "`summary`, `obligations`, `risks`, `key_dates`, `parties`, `risk_clauses`."
    + "\n\n"
    + "`summary`: one concise paragraph."
    + "\n`obligations`: list of strings (at least 1 item)."
    + "\n`risks`: list of strings (at least 1 item)."
    + "\n`key_dates`: list of strings (can be empty [])."
    + "\n`parties`: list of strings (at least 1 item)."
    + "\n`risk_clauses`: list of objects, each with `title`, `score` (0-100 integer), and `reason`."
    + "\n\nReturn ONLY valid JSON — no markdown fences, no trailing commas, no extra text."
)


def _clean_json_candidate(text: str) -> str:
    """Backwards-compatible shim — delegates to json_utils.clean_llm_json."""
    return clean_llm_json(text) or text


def _first_json_object(text: str) -> str | None:
    """Backwards-compatible shim — delegates to json_utils.clean_llm_json."""
    return clean_llm_json(text)


class MalformedAnalysisError(RuntimeError):
    pass


class AnalysisService:
    async def analyze(self, text: str) -> AnalysisResponse:
        prompt = ANALYSIS_SYSTEM_PROMPT + "\n\nContract text:\n\n" + text
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw)

    def _parse(self, raw: str) -> AnalysisResponse:
        candidate = clean_llm_json(raw)
        if candidate is None:
            raise MalformedAnalysisError("No JSON object found in the LLM response")
        try:
            parsed = AnalysisResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedAnalysisError(
                f"LLM response did not match the expected analysis schema: {exc}"
            ) from exc
        return parsed


async def analyze_document(text: str, service: AnalysisService | None = None) -> AnalysisResponse:
    service = service or AnalysisService()
    try:
        return await service.analyze(text)
    except MalformedAnalysisError:
        logger.warning("First analysis parse failed, retrying once")
        try:
            return await service.analyze(text)
        except MalformedAnalysisError as exc:
            logger.error("Analysis retry failed: %s", exc)
            raise RuntimeError("Analysis failed after retry") from exc

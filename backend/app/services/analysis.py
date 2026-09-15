import logging

from app.schemas.analysis import AnalysisResponse, RiskClause
from app.services.llm import LEGAL_DISCLAIMER, llm_client

logger = logging.getLogger(__name__)


ANALYSIS_SYSTEM_PROMPT = (
    LEGAL_DISCLAIMER
    + "\n\n"
    + "Extract the following from the contract text below and return ONLY a single JSON object with these exact keys: "
    + "`summary`, `obligations`, `risks`, `key_dates`, `parties`, `risk_clauses`."
    + "\n\n"
    + "`summary`: one concise paragraph."
    + "\n`obligations`: list of strings."
    + "\n`risks`: list of strings."
    + "\n`key_dates`: list of strings."
    + "\n`parties`: list of strings."
    + "\n`risk_clauses`: list of objects, each with `title`, `score` (0-100), and `reason`."
)


def _clean_json_candidate(text: str) -> str:
    text = text.strip()
    for marker in ['```json', '```', '```JSON']:
        if marker in text:
            start = text.find(marker)
            if start != -1:
                text = text[start + len(marker):].strip()
                break
    if text.startswith("```"):
        text = text[3:].strip()
    if text.startswith("{"):
        end = text.rfind("}")
        if end != -1:
            text = text[: end + 1]
    return text.strip()


def _first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start: index + 1]
                if candidate.count('"') % 2 == 0:
                    return candidate
    return None


class MalformedAnalysisError(RuntimeError):
    pass


class AnalysisService:
    async def analyze(self, text: str) -> AnalysisResponse:
        prompt = ANALYSIS_SYSTEM_PROMPT + "\n\nContract text:\n\n" + text
        raw = await llm_client.complete(prompt, system_prompt="")
        return self._parse(raw)

    def _parse(self, raw: str) -> AnalysisResponse:
        candidate = _first_json_object(_clean_json_candidate(raw))
        if candidate is None:
            raise MalformedAnalysisError("No JSON object found in the LLM response")
        try:
            parsed = AnalysisResponse.model_validate_json(candidate)
        except Exception as exc:
            raise MalformedAnalysisError("LLM response did not match the expected analysis schema") from exc
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

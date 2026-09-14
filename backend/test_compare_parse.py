"""Test that the comparison parser can handle a realistic LLM response.

Self-contained: copies parsing helpers from analysis.py to avoid importing
llm_client (which requires GROQ_API_KEY at module load).
"""
import json
from app.schemas.comparison import ComparisonResponse, ClauseDifference


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
                candidate = text[start:index + 1]
                if candidate.count('"') % 2 == 0:
                    return candidate
    return None


def test_parse_good_response() -> None:
    raw = """```json
{
  "summary": "Version B extends payment terms and shortens confidentiality.",
  "differences": [
    {
      "clause": "Payment terms",
      "in_a": "pay within 30 days",
      "in_b": "pay within 60 days",
      "favors": "party_b",
      "reason": "Longer payment window benefits the payer.",
      "context_for_role": "As Buyer, more time to pay improves cash flow."
    }
  ]
}
```"""
    candidate = _first_json_object(_clean_json_candidate(raw))
    assert candidate is not None, "No JSON object found"
    parsed = ComparisonResponse.model_validate_json(candidate)
    assert parsed.summary.startswith("Version B")
    assert len(parsed.differences) == 1
    assert parsed.differences[0].favors == "party_b"
    print("OK: good response parsed")


def test_parse_with_thinking_blocks() -> None:
    raw = """Here is my analysis:

<think>
I need to compare the two versions...
</think>

```json
{
  "summary": "Some changes found.",
  "differences": [
    {
      "clause": "X",
      "in_a": "a",
      "in_b": "b",
      "favors": "neutral",
      "reason": "r",
      "context_for_role": "c"
    }
  ]
}
```"""
    candidate = _first_json_object(_clean_json_candidate(raw))
    assert candidate is not None
    parsed = ComparisonResponse.model_validate_json(candidate)
    assert parsed.summary == "Some changes found."
    print("OK: response with thinking blocks parsed")


def test_parse_plain_json() -> None:
    raw = '{"summary": "plain", "differences": [{"clause": "X", "in_a": "a", "in_b": "b", "favors": "neutral", "reason": "r", "context_for_role": "c"}]}'
    candidate = _first_json_object(_clean_json_candidate(raw))
    assert candidate is not None
    parsed = ComparisonResponse.model_validate_json(candidate)
    assert parsed.differences[0].favors == "neutral"
    print("OK: plain JSON parsed")


if __name__ == "__main__":
    test_parse_good_response()
    test_parse_with_thinking_blocks()
    test_parse_plain_json()
    print("ALL OK")

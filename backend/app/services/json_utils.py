"""Robust JSON extraction utilities for LLM responses.

LLMs commonly return JSON in several imperfect forms:
  - Wrapped in ```json ... ``` markdown fences
  - With trailing commas before closing brackets/braces
  - With extra preamble or postamble text around the JSON object
  - Truncated mid-stream due to max_tokens cutoff
  - With single quotes instead of double quotes (rare)
  - With unescaped newlines inside string values

This module provides a hardened extraction pipeline used by all service parsers.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# Regex to strip trailing commas before ] or }
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])", re.MULTILINE)

# All known markdown code-fence markers
_FENCE_MARKERS = ["```json", "```JSON", "```Json", "```"]


def strip_markdown_fence(text: str) -> str:
    """Remove ```json ... ``` fencing around LLM output."""
    text = text.strip()
    for marker in _FENCE_MARKERS:
        if marker in text:
            start = text.find(marker)
            after_marker = text[start + len(marker):]
            # Find closing fence
            end_fence = after_marker.find("```")
            if end_fence != -1:
                text = after_marker[:end_fence].strip()
            else:
                text = after_marker.strip()
            break
    return text.strip()


def fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before ] or } (common LLM mistake)."""
    return _TRAILING_COMMA_RE.sub(r"\1", text)


def extract_first_json_object(text: str) -> str | None:
    """Extract the first complete JSON object from arbitrary text.

    Uses bracket-depth tracking to find the outermost {} block,
    correctly handling strings (including escaped quotes).

    Returns:
        The raw JSON string (not parsed), or None if not found.
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(text)):
        ch = text[idx]

        if escape:
            escape = False
            continue

        if ch == "\\" and in_string:
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start: idx + 1]

    return None


def clean_llm_json(raw: str) -> str | None:
    """Full cleaning pipeline for LLM-generated JSON.

    Steps:
    1. Strip markdown fences.
    2. Remove leading preamble text before '{'.
    3. Fix trailing commas.
    4. Extract first complete JSON object.

    Returns:
        A cleaned JSON string ready for json.loads(), or None.
    """
    text = strip_markdown_fence(raw)
    text = fix_trailing_commas(text)
    candidate = extract_first_json_object(text)
    if candidate:
        # One more pass of trailing comma fix inside the extracted block
        candidate = fix_trailing_commas(candidate)
    return candidate


def safe_parse_json(raw: str) -> dict | None:
    """Try to parse LLM output as JSON with full cleaning applied.

    Returns the parsed dict, or None on total failure.
    Logs a warning on failure for debugging.
    """
    candidate = clean_llm_json(raw)
    if candidate is None:
        logger.warning("JSON extraction found no object in LLM response (len=%d)", len(raw))
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode failed after cleaning: %s | snippet: %.200s", e, candidate[:200])
        return None

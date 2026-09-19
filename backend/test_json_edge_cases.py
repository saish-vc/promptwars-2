"""Comprehensive JSON parsing edge-case tests for LLM response handling.

Tests every real-world LLM output failure mode:
  1. Clean JSON                         → must parse perfectly
  2. Markdown-fenced ```json ... ```     → must strip fence and parse
  3. Trailing commas                     → must fix and parse
  4. Preamble text before JSON           → must skip and find object
  5. Postamble text after JSON           → must stop at closing brace
  6. Truncated / incomplete JSON         → must return None gracefully
  7. Single-element arrays (not broken)  → must parse
  8. Nested markdown inside JSON strings → must handle escaped quotes
  9. Empty string                        → must return None gracefully
 10. All-whitespace string               → must return None gracefully
 11. JSON with Unicode characters        → must parse correctly
 12. Full pipeline: all 5 service parsers (analysis, compare, checklist,
     negotiation, rag) against realistic LLM outputs with fences + commas.
"""

from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from app.services.json_utils import (
    clean_llm_json,
    extract_first_json_object,
    fix_trailing_commas,
    safe_parse_json,
    strip_markdown_fence,
)
from app.services.analysis import AnalysisService, MalformedAnalysisError
from app.services.comparison import ComparisonService, MalformedComparisonError
from app.services.checklist import ChecklistService, MalformedChecklistError
from app.services.negotiation import NegotiationService, MalformedNegotiationError
from app.services.rag import RAGService, MalformedRAGError


# ── 1. strip_markdown_fence ────────────────────────────────────────────────────

class TestStripMarkdownFence:
    def test_strips_json_fence(self):
        raw = '```json\n{"key": "value"}\n```'
        assert strip_markdown_fence(raw) == '{"key": "value"}'

    def test_strips_bare_fence(self):
        raw = '```\n{"key": "value"}\n```'
        assert strip_markdown_fence(raw) == '{"key": "value"}'

    def test_no_fence_unchanged(self):
        raw = '{"key": "value"}'
        assert strip_markdown_fence(raw) == raw

    def test_mixed_case_fence(self):
        raw = '```JSON\n{"a": 1}\n```'
        assert strip_markdown_fence(raw) == '{"a": 1}'

    def test_strips_leading_trailing_whitespace(self):
        raw = '   ```json\n  {"x": 1}  \n```   '
        result = strip_markdown_fence(raw)
        assert result.strip() == '{"x": 1}'


# ── 2. fix_trailing_commas ─────────────────────────────────────────────────────

class TestFixTrailingCommas:
    def test_trailing_comma_in_array(self):
        raw = '{"items": ["a", "b",]}'
        result = fix_trailing_commas(raw)
        assert json.loads(result) == {"items": ["a", "b"]}

    def test_trailing_comma_in_object(self):
        raw = '{"a": 1, "b": 2,}'
        result = fix_trailing_commas(raw)
        assert json.loads(result) == {"a": 1, "b": 2}

    def test_multiple_trailing_commas(self):
        raw = '{"arr": [1, 2,], "obj": {"x": 1,}}'
        result = fix_trailing_commas(raw)
        parsed = json.loads(result)
        assert parsed == {"arr": [1, 2], "obj": {"x": 1}}

    def test_no_trailing_commas_unchanged(self):
        raw = '{"a": [1, 2], "b": 3}'
        result = fix_trailing_commas(raw)
        assert json.loads(result) == {"a": [1, 2], "b": 3}


# ── 3. extract_first_json_object ───────────────────────────────────────────────

class TestExtractFirstJsonObject:
    def test_plain_json(self):
        raw = '{"key": "val"}'
        assert extract_first_json_object(raw) == '{"key": "val"}'

    def test_json_with_preamble(self):
        raw = 'Here is the JSON response:\n{"key": "val"}'
        result = extract_first_json_object(raw)
        assert result == '{"key": "val"}'

    def test_json_with_postamble(self):
        raw = '{"key": "val"} This is additional LLM commentary.'
        result = extract_first_json_object(raw)
        assert result == '{"key": "val"}'

    def test_nested_object(self):
        raw = '{"outer": {"inner": 1}}'
        result = extract_first_json_object(raw)
        assert json.loads(result) == {"outer": {"inner": 1}}

    def test_no_json_returns_none(self):
        assert extract_first_json_object("No JSON here at all.") is None

    def test_empty_string_returns_none(self):
        assert extract_first_json_object("") is None

    def test_quoted_braces_not_confused(self):
        raw = '{"msg": "contains } a brace", "key": 1}'
        result = extract_first_json_object(raw)
        parsed = json.loads(result)
        assert parsed["key"] == 1

    def test_escaped_quotes_in_string(self):
        raw = '{"msg": "She said \\"hello\\"", "n": 5}'
        result = extract_first_json_object(raw)
        parsed = json.loads(result)
        assert parsed["n"] == 5


# ── 4. clean_llm_json — full pipeline ─────────────────────────────────────────

class TestCleanLlmJson:
    def test_clean_plain(self):
        raw = '{"a": 1}'
        assert clean_llm_json(raw) is not None
        assert json.loads(clean_llm_json(raw)) == {"a": 1}

    def test_clean_fenced_with_trailing_comma(self):
        raw = '```json\n{"items": [1, 2,]}\n```'
        result = clean_llm_json(raw)
        assert result is not None
        assert json.loads(result) == {"items": [1, 2]}

    def test_clean_preamble_fence_trailing_comma(self):
        raw = (
            "Sure! Here is your JSON:\n"
            "```json\n"
            '{"summary": "A legal notice.", "risks": ["risk1", "risk2",],}\n'
            "```\n"
            "Let me know if you need more!"
        )
        result = clean_llm_json(raw)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["summary"] == "A legal notice."
        assert parsed["risks"] == ["risk1", "risk2"]

    def test_truncated_json_returns_none(self):
        raw = '{"summary": "A notice.", "risks": ["missing close'
        result = clean_llm_json(raw)
        assert result is None  # truncated — no complete object

    def test_empty_returns_none(self):
        assert clean_llm_json("") is None

    def test_whitespace_only_returns_none(self):
        assert clean_llm_json("   \n\t  ") is None

    def test_unicode_preserved(self):
        raw = '{"party": "Müller GmbH", "amount": "€50,000"}'
        result = clean_llm_json(raw)
        parsed = json.loads(result)
        assert parsed["party"] == "Müller GmbH"

    def test_deeply_nested(self):
        raw = '{"a": {"b": {"c": {"d": "deep"}}}}'
        result = clean_llm_json(raw)
        parsed = json.loads(result)
        assert parsed["a"]["b"]["c"]["d"] == "deep"


# ── 5. safe_parse_json ─────────────────────────────────────────────────────────

class TestSafeParseJson:
    def test_valid_json(self):
        result = safe_parse_json('{"x": 42}')
        assert result == {"x": 42}

    def test_fenced_json(self):
        result = safe_parse_json('```json\n{"x": 99}\n```')
        assert result == {"x": 99}

    def test_no_json_returns_none(self):
        result = safe_parse_json("I cannot answer that.")
        assert result is None

    def test_truncated_returns_none(self):
        result = safe_parse_json('{"key": "val')
        assert result is None


# ── 6. AnalysisService._parse edge cases ──────────────────────────────────────

class TestAnalysisServiceParse:
    def _valid_raw(self) -> str:
        return json.dumps({
            "summary": "Legal notice demanding payment.",
            "obligations": ["Pay $90,000 within 15 days"],
            "risks": ["Platform termination", "Litigation"],
            "key_dates": ["2026-10-04"],
            "parties": ["Apex Inc.", "Vanguard LLC"],
            "risk_clauses": [
                {"title": "Section 9.5", "score": 95, "reason": "High liquidated damages"},
            ],
        })

    def test_valid_plain_json(self):
        svc = AnalysisService()
        result = svc._parse(self._valid_raw())
        assert result.summary.startswith("Legal notice")
        assert len(result.risks) == 2

    def test_valid_fenced_json(self):
        svc = AnalysisService()
        raw = f"```json\n{self._valid_raw()}\n```"
        result = svc._parse(raw)
        assert result.summary.startswith("Legal notice")

    def test_trailing_comma_in_analysis(self):
        svc = AnalysisService()
        raw = (
            '{"summary": "Test.", "obligations": ["Obey",], "risks": ["Risk",],'
            ' "key_dates": [], "parties": ["A",], "risk_clauses": [{"title": "T", "score": 80, "reason": "R"},]}'
        )
        result = svc._parse(raw)
        assert result.obligations == ["Obey"]

    def test_preamble_then_json(self):
        svc = AnalysisService()
        raw = f"Here is my analysis:\n{self._valid_raw()}\n\nThat's all."
        result = svc._parse(raw)
        assert len(result.parties) == 2

    def test_no_json_raises(self):
        svc = AnalysisService()
        with pytest.raises(MalformedAnalysisError):
            svc._parse("Sorry, I cannot analyze that.")

    def test_wrong_schema_raises(self):
        svc = AnalysisService()
        with pytest.raises(MalformedAnalysisError):
            svc._parse('{"wrong_field": "bad"}')


# ── 7. ComparisonService._parse edge cases ─────────────────────────────────────

class TestComparisonServiceParse:
    def _valid_raw(self) -> str:
        return json.dumps({
            "summary": "Contract A demands full payment; Contract B proposes partial cure.",
            "differences": [{
                "clause": "Payment",
                "in_a": "$90,000 due Oct 4",
                "in_b": "$55,000 conditional cure by Oct 15",
                "favors": "buyer",
                "reason": "Reduced immediate obligation",
                "context_for_role": "Protects licensee cash flow",
            }],
        })

    def test_valid_parse(self):
        svc = ComparisonService()
        result = svc._parse(self._valid_raw())
        assert result.differences[0].favors == "buyer"

    def test_fenced_with_trailing_comma(self):
        svc = ComparisonService()
        raw = (
            "```json\n"
            '{"summary": "Compare.", "differences": [{"clause": "Pay", "in_a": "A", "in_b": "B",'
            ' "favors": "seller", "reason": "R", "context_for_role": "C"},]}\n'
            "```"
        )
        result = svc._parse(raw)
        assert result.differences[0].favors == "seller"

    def test_invalid_favors_normalized_to_neutral(self):
        svc = ComparisonService()
        raw = json.dumps({
            "summary": "Test.",
            "differences": [{
                "clause": "X", "in_a": "a", "in_b": "b",
                "favors": "unknown_party",
                "reason": "r", "context_for_role": "c",
            }],
        })
        result = svc._parse(raw)
        assert result.differences[0].favors == "neutral"

    def test_no_json_raises(self):
        svc = ComparisonService()
        with pytest.raises(MalformedComparisonError):
            svc._parse("No JSON here.")


# ── 8. ChecklistService._parse edge cases ─────────────────────────────────────

class TestChecklistServiceParse:
    def _valid_raw(self) -> str:
        return json.dumps({
            "checklist": [
                {"item": "Freeze API integrations", "status": "pending"},
                {"item": "Audit SLA logs", "status": "pending"},
            ],
            "lawyer_questions": [
                {"question": "Is the penalty enforceable?", "context": "Section 9.5"},
            ],
        })

    def test_valid_parse(self):
        svc = ChecklistService()
        result = svc._parse(self._valid_raw())
        assert len(result.checklist) == 2
        assert len(result.lawyer_questions) == 1

    def test_fenced_trailing_comma(self):
        svc = ChecklistService()
        raw = (
            "```json\n"
            '{"checklist": [{"item": "Do X", "status": "pending"},], '
            '"lawyer_questions": [{"question": "Q?", "context": "Ctx"},]}\n'
            "```"
        )
        result = svc._parse(raw)
        assert result.checklist[0].item == "Do X"

    def test_no_json_raises(self):
        svc = ChecklistService()
        with pytest.raises(MalformedChecklistError):
            svc._parse("I don't know.")


# ── 9. NegotiationService._parse edge cases ────────────────────────────────────

class TestNegotiationServiceParse:
    def _valid_raw(self) -> str:
        return json.dumps({
            "counter_clause": "Section 9.5 (Revised): Parties shall mediate first.",
            "talking_points": [
                "Cite NY precedent on liquidated damages",
                "Highlight 36.4 hours of SLA downtime",
                "Demonstrate webhook compliance with partner docs",
            ],
        })

    def test_valid_parse(self):
        svc = NegotiationService()
        result = svc._parse(self._valid_raw())
        assert len(result.talking_points) == 3

    def test_fenced_parse(self):
        svc = NegotiationService()
        raw = f"```json\n{self._valid_raw()}\n```"
        result = svc._parse(raw)
        assert "mediate" in result.counter_clause

    def test_trailing_comma_in_talking_points(self):
        svc = NegotiationService()
        raw = '{"counter_clause": "New clause.", "talking_points": ["Point A", "Point B",]}'
        result = svc._parse(raw)
        assert result.talking_points == ["Point A", "Point B"]

    def test_no_json_raises(self):
        svc = NegotiationService()
        with pytest.raises(MalformedNegotiationError):
            svc._parse("Sorry, cannot generate.")


# ── 10. RAGService._parse edge cases ──────────────────────────────────────────

class TestRAGServiceParse:
    CONTEXT = "within fifteen (15) calendar days from receipt hereof (no later than October 4, 2026)"

    def _valid_raw(self) -> str:
        return json.dumps({
            "answer": "The cure deadline is October 4, 2026.",
            "confidence": 0.97,
            "sources": [
                {"text": "within fifteen (15) calendar days from receipt hereof", "page": 1},
            ],
        })

    def test_valid_parse(self):
        svc = RAGService()
        result = svc._parse(self._valid_raw(), self.CONTEXT)
        assert result.confidence == 0.97
        assert result.confidence_score == 0.97

    def test_fenced_parse(self):
        svc = RAGService()
        raw = f"```json\n{self._valid_raw()}\n```"
        result = svc._parse(raw, self.CONTEXT)
        assert result.confidence == 0.97

    def test_trailing_comma_in_sources(self):
        svc = RAGService()
        raw = (
            '{"answer": "Oct 4, 2026.", "confidence": 0.9, '
            '"sources": [{"text": "within fifteen (15) calendar days from receipt hereof", "page": 1},]}'
        )
        result = svc._parse(raw, self.CONTEXT)
        assert result.confidence == 0.9

    def test_preamble_text(self):
        svc = RAGService()
        raw = f"Based on the contract:\n{self._valid_raw()}\nLet me know if you have questions."
        result = svc._parse(raw, self.CONTEXT)
        assert "October 4" in result.answer

    def test_no_json_raises(self):
        svc = RAGService()
        with pytest.raises(MalformedRAGError):
            svc._parse("I cannot answer.", self.CONTEXT)

    def test_source_filtered_if_not_in_context(self):
        """Sources with text NOT in context and length > 200 chars should be filtered out."""
        svc = RAGService()
        long_hallucination = "X" * 201
        raw = json.dumps({
            "answer": "Answer here.",
            "confidence": 0.8,
            "sources": [
                {"text": long_hallucination, "page": 1},       # should be filtered
                {"text": "short snippet", "page": 2},           # should stay (short)
            ],
        })
        result = svc._parse(raw, "some context")
        # long hallucination not in context and len > 200 → filtered
        texts = [s.text for s in result.sources]
        assert long_hallucination not in texts
        assert "short snippet" in texts


# ── Main runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("[RUNNING] JSON PARSING EDGE-CASE TEST SUITE")
    print("=" * 70 + "\n")

    import unittest

    # Convert pytest-style classes to unittest for standalone run
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for cls in [
        TestStripMarkdownFence,
        TestFixTrailingCommas,
        TestExtractFirstJsonObject,
        TestCleanLlmJson,
        TestSafeParseJson,
        TestAnalysisServiceParse,
        TestComparisonServiceParse,
        TestChecklistServiceParse,
        TestNegotiationServiceParse,
        TestRAGServiceParse,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\n{'=' * 70}")
    print(f"JSON Edge-Case Tests: {passed}/{result.testsRun} PASSED")
    print("=" * 70)
    sys.exit(0 if result.wasSuccessful() else 1)

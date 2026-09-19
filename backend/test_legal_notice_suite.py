"""Comprehensive Real-Life Legal Notice Test Suite.

Simulates an authentic legal notice workflow end-to-end:
1. Ingestion: Ingests a formal Notice of Material Breach & Cease-and-Desist Demand.
2. Analysis (Risk Audit): Audits obligations, risks, key dates, parties, and clause scores.
3. Comparison: Compares initial breach demand against recipient's cure response.
4. Checklist: Generates operational checklist and lawyer questions.
5. Negotiation: Generates replacement counter-clause and tactical talking points.
6. Chat (RAG): Answers specific legal questions with cited sources and confidence score.
7. Export: Assembles the complete Lawyer Pack report.
8. Edge Cases: Tests 422, 404, empty inputs, and health endpoints.
"""

from __future__ import annotations

import asyncio
import os
import sys
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.schemas.analysis import AnalysisResponse, RiskClause
from app.schemas.checklist import ChecklistResponse, ChecklistItem, LawyerQuestion
from app.schemas.comparison import ComparisonResponse, ClauseDifference
from app.schemas.negotiation import NegotiationResponse
from app.schemas.chat import ChatResponse, SourceSnippet

# ── Realistic Legal Notice Test Documents ─────────────────────────────────────

REAL_LEGAL_NOTICE = """
FORMAL NOTICE OF MATERIAL BREACH OF MASTER SAAS AGREEMENT
AND DEMAND FOR IMMEDIATE CURE / CEASE AND DESIST

DATE: September 19, 2026
SENT VIA CERTIFIED ELECTRONIC MAIL AND REGISTERED POST

FROM:
Apex Enterprise Solutions Inc. ("Licensor")
100 Financial Center Parkway, Suite 1400
New York, NY 10005

TO:
Vanguard Logistics Technologies LLC ("Licensee")
840 Ocean Boulevard, Suite 500
Miami, FL 33139
Attn: Legal & Compliance Department

RE: Notice of Default under Master SaaS Agreement dated January 15, 2025

Dear Legal Department,

PLEASE TAKE NOTICE that Licensee is in material breach of the Master SaaS Agreement (the "Agreement") entered into between Licensor and Licensee on January 15, 2025:

1. MONETARY DEFAULT (SECTION 3.2):
Under Section 3.2 of the Agreement, Licensee is obligated to remit recurring monthly platform fees of $45,000.00 within thirty (30) days of invoice date. As of the date hereof, Invoice #INV-2026-0819 ($45,000.00 due July 31, 2026) and Invoice #INV-2026-0919 ($45,000.00 due August 31, 2026) remain unpaid, representing an aggregate overdue sum of $90,000.00.

2. UNAUTHORIZED API EXPLOITATION & IP INFRINGEMENT (SECTION 9.4):
Forensic log analysis revealed unauthorized high-frequency automated scraping scripts executing against Licensor's proprietary pricing algorithms between August 12, 2026 and August 28, 2026. This activity violates Section 9.4 (Proprietary Rights and Reverse Engineering Restrictions).

3. FORMAL DEMAND FOR CURE:
Pursuant to Section 14.2 of the Agreement, Licensee is hereby provided with formal notice requiring full cure of the aforesaid defaults within fifteen (15) calendar days from receipt hereof (no later than October 4, 2026 at 5:00 PM Eastern Standard Time). Cure requires:
  (a) Wire transfer of $90,000.00 in immediately available funds; and
  (b) Written certification affirming complete cessation of unauthorized scraping activities.

4. REMEDIES AND LIQUIDATED DAMAGES:
Should Licensee fail to cure by October 4, 2026, Licensor will immediately terminate platform access under Section 14.3, accelerate the remaining term licensing balance of $360,000.00, and enforce the $250,000.00 contractual liquidated damages penalty under Section 9.5, together with reasonable attorney fees and costs under Section 18.2.

5. GOVERNING LAW:
This Notice and all disputes arising hereunder shall be governed by the laws of the State of New York.

Sincerely,
Apex Enterprise Solutions Inc.
By: Eleanor Vance, General Counsel
"""

REAL_COUNTER_RESPONSE = """
RESPONSE TO NOTICE OF ALLEGED MATERIAL BREACH
AND PROPOSAL FOR CONDITIONAL CURE AND MEDIATION

DATE: September 22, 2026

FROM:
Vanguard Logistics Technologies LLC ("Licensee")
840 Ocean Boulevard, Suite 500, Miami, FL 33139

TO:
Apex Enterprise Solutions Inc. ("Licensor")
100 Financial Center Parkway, Suite 1400, New York, NY 10005

RE: Rebuttal and Proposed Resolution to Notice dated September 19, 2026

Dear Ms. Vance,

Licensee receipt of your letter dated September 19, 2026 is acknowledged. Licensee expressly disputes several assertions:

1. SERVICE CREDITS & DISPUTED INVOICES:
Under Service Level Agreement (SLA) Section 4.3, Licensor experienced 36.4 hours of unscheduled system downtime across July and August 2026. Licensee is entitled to $35,000.00 in verified SLA credits. Licensee tenders conditional payment of $55,000.00 in full settlement of overdue fees by October 15, 2026.

2. API DATA INTEGRATION:
The automated queries cited in your letter were conducted via documented partner webhooks for freight synchronization and do not constitute reverse engineering or proprietary infringement under Section 9.1. Licensee invites a joint forensic audit.

3. REJECTION OF LIQUIDATED DAMAGES & ACCELERATION:
Licensee rejects the $250,000.00 liquidated damages demand as an unenforceable penalty under Florida and New York law and requests immediate senior executive mediation under Section 17.1 before any litigation is initiated.

Sincerely,
Vanguard Logistics Technologies LLC
By: Marcus Thorne, Chief Operating Officer
"""


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def test_suite():
    print("\n" + "=" * 70)
    print("[RUNNING] COMPREHENSIVE LEGAL NOTICE SUITE (7 STAGES + EDGE CASES)")
    print("=" * 70 + "\n")

    with TestClient(app) as client:
        # ── 0. Healthcheck ────────────────────────────────────────────────────
        print("▶ Stage 0: Health Endpoint Verification")
        res = client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data.get("status") in ["ok", "healthy"]
        print("  ✔ Health endpoint healthy:", data)

        # ── 1. Document Ingestion (Paste & Upload) ─────────────────────────────
        print("\n▶ Stage 1: Document Ingestion (Paste & File Upload)")
        # 1a: Paste legal notice
        res_paste = client.post(
            "/documents/paste",
            json={"text": REAL_LEGAL_NOTICE, "filename": "Formal_Breach_Notice.txt"},
        )
        assert res_paste.status_code == 200, f"Paste failed: {res_paste.text}"
        doc_data = res_paste.json()
        doc_id = doc_data["doc_id"]
        assert len(doc_id) > 0
        assert "FORMAL NOTICE OF MATERIAL BREACH" in doc_data["text"]
        print(f"  ✔ Document pasted successfully. Assigned doc_id={doc_id}")

        # 1b: Upload via file multipart
        file_bytes = REAL_COUNTER_RESPONSE.encode("utf-8")
        res_upload = client.post(
            "/documents/upload",
            files={"file": ("Counter_Response.txt", BytesIO(file_bytes), "text/plain")},
        )
        assert res_upload.status_code == 200, f"Upload failed: {res_upload.text}"
        counter_doc_id = res_upload.json()["doc_id"]
        print(f"  ✔ Counter-response uploaded successfully. Assigned doc_id={counter_doc_id}")

        # ── 2. Risk Audit / Analysis ──────────────────────────────────────────
        print("\n▶ Stage 2: Risk Audit & Clause Scoring")
        mock_analysis = AnalysisResponse(
            summary="Formal demand for cure citing $90,000 unpaid SaaS platform fees and alleged reverse engineering/scraping.",
            obligations=[
                "Remit $90,000 overdue fees by October 4, 2026",
                "Provide written certification of cessation of automated scraping",
            ],
            risks=[
                "Immediate platform access termination under Section 14.3",
                "Acceleration of remaining $360,000 contract fees",
                "$250,000 liquidated damages enforcement under Section 9.5",
                "Litigation under New York governing law with attorney fees",
            ],
            key_dates=["2026-10-04 (5:00 PM EST)", "15 calendar days from receipt"],
            parties=["Apex Enterprise Solutions Inc.", "Vanguard Logistics Technologies LLC"],
            risk_clauses=[
                RiskClause(
                    title="Section 9.5 Liquidated Damages",
                    score=95,
                    reason="$250,000 penalty clause triggered automatically upon failure to cure",
                ),
                RiskClause(
                    title="Section 14.3 Contract Acceleration",
                    score=90,
                    reason="Acceleration of entire $360,000 remaining term balance",
                ),
                RiskClause(
                    title="Section 14.2 Cure Period",
                    score=80,
                    reason="Short 15-day timeline creates urgent default vulnerability",
                ),
            ],
        )

        with patch("app.routers.analyze.analyze_document", return_value=mock_analysis):
            # Test /analyze/contract with doc_id (frontend route)
            res_analysis = client.post("/analyze/contract", json={"doc_id": doc_id})
            assert res_analysis.status_code == 200, f"Analysis failed: {res_analysis.text}"
            analysis_json = res_analysis.json()
            assert len(analysis_json["obligations"]) == 2
            assert len(analysis_json["risks"]) == 4
            assert analysis_json["risk_clauses"][0]["score"] == 95
            print("  ✔ Risk audit analyzed via /analyze/contract (doc_id):")
            print(f"    - Summary: {analysis_json['summary'][:70]}...")
            print(f"    - High Risk Clause: {analysis_json['risk_clauses'][0]['title']} ({analysis_json['risk_clauses'][0]['score']}/100)")

            # Test /analyze/document with direct text
            res_doc = client.post("/analyze/document", json={"text": REAL_LEGAL_NOTICE})
            assert res_doc.status_code == 200
            print("  ✔ Direct text analysis verified via /analyze/document")

        # ── 3. Document Comparison ────────────────────────────────────────────
        print("\n▶ Stage 3: Comparison (Breach Notice vs Counter Proposal)")
        mock_diff = ComparisonResponse(
            summary="Licensor demands $90,000 and $250k penalty; Licensee claims $35k SLA credits and proposes $55k conditional cure with mediation.",
            differences=[
                ClauseDifference(
                    clause="Monetary Obligation",
                    in_a="Full $90,000 overdue sum due by Oct 4",
                    in_b="$55,000 conditional cure factoring $35,000 SLA credits due by Oct 15",
                    favors="buyer",
                    reason="Significant reduction in immediate cash outlay and recognition of service disruption credits",
                    context_for_role="Protects Licensee cash flow and asserts legitimate SLA penalty against Licensor",
                ),
                ClauseDifference(
                    clause="Liquidated Damages and Litigation",
                    in_a="Threatens immediate $250,000 penalty and NY court action",
                    in_b="Rejects penalty as legally unenforceable and demands pre-suit mediation",
                    favors="buyer",
                    reason="Defuses immediate penalty exposure and shifts dispute into private executive mediation",
                    context_for_role="Prevents catastrophic fee acceleration and halts premature litigation",
                ),
            ],
        )

        with patch("app.routers.compare.compare_contracts", return_value=mock_diff):
            res_compare = client.post(
                "/compare/contracts",
                json={
                    "document_a": {"doc_id": doc_id},
                    "document_b": {"doc_id": counter_doc_id},
                    "user_role": "Licensee",
                },
            )
            assert res_compare.status_code == 200, f"Comparison failed: {res_compare.text}"
            comp_json = res_compare.json()
            assert len(comp_json["differences"]) >= 1
            print("  ✔ Comparison executed successfully:")
            print(f"    - Differences identified: {len(comp_json['differences'])}")
            print(f"    - Favors: {comp_json['differences'][0]['favors'].upper()} ({comp_json['differences'][0]['clause']})")

        # ── 4. Action Checklist ───────────────────────────────────────────────
        print("\n▶ Stage 4: Action Checklist & Lawyer Questions")
        mock_checklist = ChecklistResponse(
            checklist=[
                ChecklistItem(item="Freeze all automated API integrations and run internal audit", status="pending"),
                ChecklistItem(item="Audit SLA downtime logs from July and August 2026", status="pending"),
                ChecklistItem(item="Prepare $55,000 escrow or settlement disbursement", status="pending"),
                ChecklistItem(item="Serve formal mediation demand before October 4 deadline", status="pending"),
            ],
            lawyer_questions=[
                LawyerQuestion(
                    question="Is the $250,000 liquidated damages clause enforceable under New York law as an unconscionable penalty?",
                    context="Section 9.5 Liquidated Damages provision",
                ),
                LawyerQuestion(
                    question="Can Licensor accelerate $360,000 future fees while also asserting liquidated damages without double recovery?",
                    context="Section 14.3 Cumulative remedies and acceleration",
                ),
            ],
        )

        with patch("app.routers.checklist.generate_checklist", return_value=mock_checklist):
            res_chk = client.post("/generate/checklist", json={"doc_id": doc_id})
            assert res_chk.status_code == 200, f"Checklist failed: {res_chk.text}"
            chk_json = res_chk.json()
            assert len(chk_json["checklist"]) == 4
            assert len(chk_json["lawyer_questions"]) == 2
            print(f"  ✔ Checklist generated with {len(chk_json['checklist'])} items and {len(chk_json['lawyer_questions'])} lawyer questions.")

        # ── 5. Negotiation Strategy ───────────────────────────────────────────
        print("\n▶ Stage 5: Negotiation Strategy & Counter-Clause")
        mock_negotiation = NegotiationResponse(
            counter_clause=(
                "Section 9.5 (Revised): In the event of an alleged technical breach, the parties shall "
                "convene a joint technical audit within ten (10) business days. Neither party shall accelerate "
                "future fees or claim liquidated damages without first completing mandatory good-faith mediation."
            ),
            talking_points=[
                "Point out that automated webhook queries followed standard partner documentation without intent to decompile.",
                "Demonstrate 36.4 hours of documented platform downtime justifying offsetting SLA fee deductions.",
                "Cite NY appellate precedent holding arbitrary lump-sum liquidated damages without actual harm proof unenforceable.",
            ],
        )

        with patch("app.routers.negotiation.generate_negotiation", return_value=mock_negotiation):
            res_neg = client.post(
                "/generate/negotiation",
                json={
                    "doc_id": doc_id,
                    "clause_topic": "Liquidated Damages $250k",
                    "user_role": "Licensee",
                },
            )
            assert res_neg.status_code == 200, f"Negotiation failed: {res_neg.text}"
            neg_json = res_neg.json()
            assert len(neg_json["talking_points"]) == 3
            print("  ✔ Negotiation strategy generated counter-clause & 3 strategic talking points.")

        # ── 6. Chat (RAG) ─────────────────────────────────────────────────────
        print("\n▶ Stage 6: Legal Notice Chat / RAG")
        mock_chat = ChatResponse(
            answer="The cure deadline is October 4, 2026, at 5:00 PM Eastern Standard Time (15 calendar days from receipt). Failure to cure allows Licensor to terminate access and seek $250,000 in liquidated damages.",
            confidence=0.98,
            confidence_score=0.98,
            sources=[
                SourceSnippet(text="within fifteen (15) calendar days from receipt hereof (no later than October 4, 2026 at 5:00 PM Eastern Standard Time)", page=1),
                SourceSnippet(text="enforce the $250,000.00 contractual liquidated damages penalty under Section 9.5", page=1),
            ],
        )

        with patch("app.routers.chat.chat_about_contract", return_value=mock_chat):
            # Test /chat/contract endpoint (called by frontend)
            res_chat = client.post(
                "/chat/contract",
                json={"doc_id": doc_id, "question": "What is the deadline to cure the breach?"},
            )
            assert res_chat.status_code == 200, f"Chat failed: {res_chat.text}"
            chat_data = res_chat.json()
            assert chat_data["confidence"] >= 0.9
            assert chat_data["confidence_score"] == chat_data["confidence"]
            assert len(chat_data["sources"]) == 2
            print("  ✔ /chat/contract verified with confidence:", chat_data["confidence_score"])
            print("    Answer:", chat_data["answer"][:80], "...")

            # Test /chat root endpoint
            res_chat_root = client.post(
                "/chat",
                json={"doc_id": doc_id, "question": "What are the remedies threatened?"},
            )
            assert res_chat_root.status_code == 200
            print("  ✔ Standard /chat endpoint verified.")

        # ── 7. Export Lawyer Pack ─────────────────────────────────────────────
        print("\n▶ Stage 7: Export Lawyer Pack")
        res_export = client.post(
            "/export/lawyer-pack",
            json={
                "doc_id": doc_id,
                "analysis": analysis_json,
                "checklist": chk_json,
                "negotiation": neg_json,
            },
        )
        assert res_export.status_code == 200, f"Export failed: {res_export.text}"
        pack_text = res_export.text
        assert "# LAWYER PACK" in pack_text
        assert "## EXECUTIVE SUMMARY" in pack_text
        assert "## RISK CLAUSE SCORECARD" in pack_text
        assert "## ACTION CHECKLIST" in pack_text
        assert "## QUESTIONS FOR YOUR LAWYER" in pack_text
        assert "## SUGGESTED COUNTER-CLAUSE" in pack_text
        assert "## NEGOTIATION TALKING POINTS" in pack_text
        print("  ✔ Complete Lawyer Pack report generated successfully:")
        print("    Report length:", len(pack_text), "characters")

        # ── 8. Edge Cases & Error Handling ────────────────────────────────────
        print("\n▶ Stage 8: Edge Cases & Error Validations")

        # 8a. Empty text on paste
        res_err1 = client.post("/documents/paste", json={"text": "   "})
        assert res_err1.status_code == 422, "Expected 422 on empty paste"
        print("  ✔ Edge case: Empty document paste correctly rejected with 422")

        # 8b. Non-existent doc_id in analysis
        res_err2 = client.post("/analyze/contract", json={"doc_id": "non_existent_id_999"})
        assert res_err2.status_code == 404, "Expected 404 on missing doc_id"
        print("  ✔ Edge case: Non-existent doc_id in analysis correctly returns 404")

        # 8c. Empty question in chat
        res_err3 = client.post("/chat/contract", json={"doc_id": doc_id, "question": "   "})
        assert res_err3.status_code == 422, "Expected 422 on empty chat question"
        print("  ✔ Edge case: Empty chat question rejected with 422")

        # 8d. Missing analysis in export
        res_err4 = client.post("/export/lawyer-pack", json={"doc_id": doc_id, "analysis": {}})
        assert res_err4.status_code == 422, "Expected 422 on missing analysis in export"
        print("  ✔ Edge case: Missing analysis in export rejected with 422")

        # 8e. Export with non-existent document
        res_err5 = client.post(
            "/export/lawyer-pack",
            json={"doc_id": "non_existent_doc_id", "analysis": {"summary": "test"}},
        )
        assert res_err5.status_code == 404, "Expected 404 on missing doc in export"
        print("  ✔ Edge case: Export for non-existent document returns 404")

        # 8f. Unmatched comparison payload
        res_err6 = client.post(
            "/compare/contracts",
            json={"document_a": {}, "document_b": {}, "user_role": "Buyer"},
        )
        assert res_err6.status_code == 422, "Expected 422 on invalid comparison input"
        print("  ✔ Edge case: Malformed compare payload rejected with 422")

    print("\n" + "=" * 70)
    print("🎉 ALL 8 STAGES & EDGE CASE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_suite()

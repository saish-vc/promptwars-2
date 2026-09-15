import json
from datetime import datetime

from app.schemas.export import LawyerPackRequest, LawyerPackResponse
from app.services.documents import DocumentStore


def generate_lawyer_pack(request: LawyerPackRequest, store: DocumentStore) -> LawyerPackResponse:
    doc_text = store.get_text(request.doc_id) or ""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    sections: list[str] = []

    sections.append(f"# LAWYER PACK\nGenerated: {now}\nDocument ID: {request.doc_id}\n")

    # --- Analysis ---
    analysis = request.analysis or {}
    sections.append("## EXECUTIVE SUMMARY")
    sections.append(analysis.get("summary", "No summary available."))

    parties = analysis.get("parties") or []
    if parties:
        sections.append("\n## PARTIES")
        for p in parties:
            sections.append(f"  - {p}")

    obligations = analysis.get("obligations") or []
    if obligations:
        sections.append("\n## OBLIGATIONS")
        for o in obligations:
            sections.append(f"  • {o}")

    risks = analysis.get("risks") or []
    if risks:
        sections.append("\n## KEY RISKS")
        for r in risks:
            sections.append(f"  ⚠ {r}")

    key_dates = analysis.get("key_dates") or []
    if key_dates:
        sections.append("\n## KEY DATES")
        for d in key_dates:
            sections.append(f"  📅 {d}")

    risk_clauses = analysis.get("risk_clauses") or []
    if risk_clauses:
        sections.append("\n## RISK CLAUSE SCORECARD")
        for clause in risk_clauses:
            title = clause.get("title", "Unknown")
            score = clause.get("score", 0)
            reason = clause.get("reason", "")
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            sections.append(f"  [{bar}] {score}/100  {title}")
            sections.append(f"    Reason: {reason}")

    # --- Checklist ---
    if request.checklist:
        checklist_items = request.checklist.get("checklist") or []
        lawyer_qs = request.checklist.get("lawyer_questions") or []
        if checklist_items:
            sections.append("\n## ACTION CHECKLIST")
            for item in checklist_items:
                status = item.get("status", "pending")
                tick = "☐" if status == "pending" else "✔" if status == "completed" else "—"
                sections.append(f"  {tick} {item.get('item', '')}")
        if lawyer_qs:
            sections.append("\n## QUESTIONS FOR YOUR LAWYER")
            for i, q in enumerate(lawyer_qs, 1):
                sections.append(f"  {i}. {q.get('question', '')}")
                sections.append(f"     Context: {q.get('context', '')}")

    # --- Negotiation ---
    if request.negotiation:
        counter = request.negotiation.get("counter_clause", "")
        talking_points = request.negotiation.get("talking_points") or []
        if counter:
            sections.append("\n## SUGGESTED COUNTER-CLAUSE")
            sections.append(counter)
        if talking_points:
            sections.append("\n## NEGOTIATION TALKING POINTS")
            for i, point in enumerate(talking_points, 1):
                sections.append(f"  {i}. {point}")

    sections.append("\n---")
    sections.append("This document provides general legal information, not legal advice.")
    sections.append("Consult a qualified lawyer before making any decisions.")

    content = "\n".join(sections)
    return LawyerPackResponse(content=content)

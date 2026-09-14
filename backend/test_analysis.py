from app.schemas.analysis import AnalysisResponse, RiskClause

example = AnalysisResponse(
    summary="Short summary.",
    obligations=["Pay by 1 June."],
    risks=["Late payment risk."],
    key_dates=["2026-06-01"],
    parties=["Acme Corp", "Beta LLC"],
    risk_clauses=[RiskClause(title="Payment", score=80, reason="High risk")],
)

data = example.model_dump_json()
parsed = AnalysisResponse.model_validate_json(data)
assert parsed.summary == "Short summary."
assert parsed.risk_clauses[0].score == 80
print("OK")

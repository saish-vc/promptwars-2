from pydantic import BaseModel, Field


class RiskClause(BaseModel):
    title: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)


class AnalysisResponse(BaseModel):
    summary: str = Field(min_length=1)
    obligations: list[str] = Field(min_length=1)
    risks: list[str] = Field(min_length=1)
    key_dates: list[str] = Field(min_length=0)
    parties: list[str] = Field(min_length=1)
    risk_clauses: list[RiskClause] = Field(min_length=1)

from typing import List

from pydantic import BaseModel, Field


class RiskClause(BaseModel):
    title: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1)


class AnalysisResponse(BaseModel):
    summary: str = Field(min_length=1)
    obligations: List[str] = Field(min_length=1)
    risks: List[str] = Field(min_length=1)
    key_dates: List[str] = Field(min_length=0)
    parties: List[str] = Field(min_length=1)
    risk_clauses: List[RiskClause] = Field(min_length=1)

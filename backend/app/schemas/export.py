from pydantic import BaseModel, Field


class LawyerPackRequest(BaseModel):
    doc_id: str = Field(min_length=1)
    analysis: dict = Field(..., description="The analysis result from Stage 3")
    checklist: dict = Field(default=None, description="Optional checklist result")
    negotiation: dict = Field(default=None, description="Optional negotiation result")


class LawyerPackResponse(BaseModel):
    content: str = Field(min_length=1, description="The lawyer pack content as text")
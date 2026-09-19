from pydantic import BaseModel, Field


class NegotiationRequest(BaseModel):
    text: str | None = Field(default=None, max_length=2_000_000)
    doc_id: str | None = Field(default=None, max_length=64)
    analysis: dict | None = Field(default=None, description="The analysis result from Stage 3")
    clause_title: str | None = Field(default=None, description="The title of the risky clause to negotiate")
    clause_topic: str | None = Field(default=None, description="Topic or clause to negotiate")
    clause_text: str | None = Field(default=None, description="The text of the risky clause")
    user_role: str = Field(default="Buyer", max_length=255, description="Which party the user represents")


class NegotiationResponse(BaseModel):
    counter_clause: str = Field(min_length=1, description="Suggested replacement clause text")
    talking_points: list = Field(min_length=1, description="List of talking points for negotiation")
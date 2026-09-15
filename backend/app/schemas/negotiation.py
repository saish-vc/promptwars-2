from pydantic import BaseModel, Field


class NegotiationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    analysis: dict = Field(..., description="The analysis result from Stage 3")
    clause_title: str = Field(min_length=1, description="The title of the risky clause to negotiate")
    clause_text: str = Field(min_length=1, description="The text of the risky clause")
    user_role: str = Field(min_length=1, max_length=255, description="Which party the user represents")


class NegotiationResponse(BaseModel):
    counter_clause: str = Field(min_length=1, description="Suggested replacement clause text")
    talking_points: list = Field(min_length=1, description="List of talking points for negotiation")
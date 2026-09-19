from pydantic import BaseModel, Field, model_validator


class ChatRequest(BaseModel):
    doc_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1000)


class SourceSnippet(BaseModel):
    text: str = Field(min_length=1)
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_score: float | None = None
    sources: list[SourceSnippet] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_confidence_score(self) -> "ChatResponse":
        if self.confidence_score is None:
            self.confidence_score = self.confidence
        return self
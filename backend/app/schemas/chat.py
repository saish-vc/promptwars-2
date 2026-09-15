from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    doc_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1000)


class SourceSnippet(BaseModel):
    text: str = Field(min_length=1)
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[SourceSnippet] = Field(min_length=0)
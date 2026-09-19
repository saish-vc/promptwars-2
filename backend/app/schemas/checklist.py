from pydantic import BaseModel, Field


class ChecklistRequest(BaseModel):
    text: str | None = Field(default=None, max_length=2_000_000)
    doc_id: str | None = Field(default=None, max_length=64)
    analysis: dict | None = Field(default=None, description="The analysis result from Stage 3")


class ChecklistItem(BaseModel):
    item: str = Field(min_length=1)
    status: str = Field(default="pending", description="pending, completed, or n/a")


class LawyerQuestion(BaseModel):
    question: str = Field(min_length=1)
    context: str = Field(min_length=1, description="Which clause or risk this relates to")


class ChecklistResponse(BaseModel):
    checklist: list[ChecklistItem] = Field(min_length=1)
    lawyer_questions: list[LawyerQuestion] = Field(min_length=1)
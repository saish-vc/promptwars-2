from typing import List

from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    doc_id: str | None = Field(default=None, max_length=64)
    text: str | None = Field(default=None, max_length=2_000_000)

    def resolve(self, store_text_fn) -> str:
        if self.text and self.text.strip():
            return self.text.strip()
        if self.doc_id:
            text = store_text_fn(self.doc_id)
            if text:
                return text
        raise ValueError("Provide either doc_id or text for each document")


class ComparisonRequest(BaseModel):
    document_a: DocumentInput = Field(...)
    document_b: DocumentInput = Field(...)
    user_role: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Which party the user represents, e.g. 'Buyer' or 'Seller'",
    )


class ClauseDifference(BaseModel):
    clause: str = Field(min_length=1)
    in_a: str = Field(min_length=1)
    in_b: str = Field(min_length=1)
    favors: str = Field(min_length=1)  # "party_a", "party_b", or "neutral"
    reason: str = Field(min_length=1)
    context_for_role: str = Field(min_length=1)


class ComparisonResponse(BaseModel):
    summary: str = Field(min_length=1)
    differences: List[ClauseDifference] = Field(min_length=1)

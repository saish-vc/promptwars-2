from pydantic import BaseModel, Field


class PasteDocumentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    filename: str | None = Field(default=None, max_length=255)


class DocumentResponse(BaseModel):
    doc_id: str
    text: str

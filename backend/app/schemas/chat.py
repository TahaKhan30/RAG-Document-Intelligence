from datetime import datetime
from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class CitedChunk(BaseModel):
    chunk_id: int
    page_number: int
    section_heading: str | None
    document_id: int
    document_title: str


class AnswerResponse(BaseModel):
    answer: str
    cited_chunks: list[CitedChunk]


class ConversationMessage(BaseModel):
    id: int
    role: str
    content: str
    cited_chunks: list | None
    created_at: datetime
    class Config:
        from_attributes = True

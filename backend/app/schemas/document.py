from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    title: str
    page_count: int
    word_count: int
    chunk_count: int
    status: str
    error_message: str | None
    uploaded_at: datetime
    indexed_at: datetime | None
    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: int
    status: str
    chunk_count: int
    error_message: str | None
    class Config:
        from_attributes = True

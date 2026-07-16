from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    chunk_id: int
    content: str
    page_number: int
    section_heading: str | None
    document_id: int
    document_title: str


class SearchResponse(BaseModel):
    results: list[SearchResult]

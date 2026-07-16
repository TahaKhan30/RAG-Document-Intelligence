"""
RAG service — orchestrates the retrieve → generate flow.

1. Retrieve relevant chunks via hybrid search
2. Build a grounded prompt with the chunks as context
3. Ask Claude to answer using ONLY the provided context
4. Return the answer plus the chunks that were cited

The system prompt forces Claude to ground answers in the context and say when it
doesn't know — this is what prevents hallucinations dressed up as confidence.
"""
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.services.retrieval_service import hybrid_search

_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a document intelligence assistant. You answer questions strictly using the provided context excerpts from the user's documents.

Rules:
- Answer ONLY from the provided context. Do not use outside knowledge.
- If the context does not contain the answer, say so clearly: "I couldn't find that in the document." Never invent facts.
- Be concise and specific.
- When you use information from a specific excerpt, the excerpts are numbered — your answer will be shown alongside the source pages, so you don't need to write citations inline.
- If excerpts conflict, note the discrepancy."""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        heading = f" — {c['section_heading']}" if c.get("section_heading") else ""
        parts.append(
            f"[Excerpt {i} | {c['document_title']}, page {c['page_number']}{heading}]\n{c['content']}"
        )
    return "\n\n".join(parts)


async def answer_question(
    db: AsyncSession,
    user_id: int,
    question: str,
    document_id: int | None = None,
) -> dict:
    """
    Returns {answer: str, cited_chunks: list[dict]}.
    cited_chunks carries the citation metadata for the UI to render source references.
    """
    chunks = await hybrid_search(db, user_id, question, document_id=document_id)

    if not chunks:
        return {
            "answer": "I couldn't find anything relevant in your documents to answer that.",
            "cited_chunks": [],
        }

    context = _build_context(chunks)
    user_message = f"Context excerpts:\n\n{context}\n\n---\n\nQuestion: {question}"

    message = await _client.messages.create(
        model=settings.CHAT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    answer = message.content[0].text.strip()

    cited = [
        {
            "chunk_id": c["chunk_id"],
            "page_number": c["page_number"],
            "section_heading": c["section_heading"],
            "document_id": c["document_id"],
            "document_title": c["document_title"],
        }
        for c in chunks
    ]

    return {"answer": answer, "cited_chunks": cited}


async def generate_summary(db: AsyncSession, user_id: int, document_id: int) -> str:
    """Generate a short summary by retrieving representative chunks and asking Claude."""
    chunks = await hybrid_search(db, user_id, "summary overview main points", document_id=document_id, top_k=8)
    if not chunks:
        return "Not enough content to summarize."

    context = _build_context(chunks)
    message = await _client.messages.create(
        model=settings.CHAT_MODEL,
        max_tokens=512,
        system="You summarize documents concisely in 3 short paragraphs based only on the provided excerpts.",
        messages=[{"role": "user", "content": f"{context}\n\n---\n\nSummarize this document."}],
    )
    return message.content[0].text.strip()

"""
Chunking service — splits document text into overlapping chunks.

Strategy: recursive character splitting with token-based sizing and overlap.
Each chunk carries its page number and a best-effort section heading so answers
can cite exactly where they came from. Overlap prevents context loss at boundaries.

Chunking quality is the single biggest driver of RAG retrieval accuracy, so this
is deliberately kept simple, debuggable, and metadata-rich rather than clever.
"""
import re
from app.core.config import settings

# Rough token estimate: ~4 chars per token for English. Good enough for chunk sizing.
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _detect_heading(text: str) -> str | None:
    """Best-effort: use the first short line as a section heading if it looks like one."""
    first_line = text.strip().split("\n")[0].strip()
    if 0 < len(first_line) <= 80 and not first_line.endswith("."):
        return first_line
    return None


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split pages into chunks.
    Returns list of {content, page_number, section_heading, chunk_index, token_count}.
    """
    chunk_size = settings.CHUNK_SIZE_TOKENS
    overlap = settings.CHUNK_OVERLAP_TOKENS
    chunk_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = overlap * CHARS_PER_TOKEN

    chunks = []
    chunk_index = 0

    for page in pages:
        page_number = page["page_number"]
        text = page["text"]
        heading = _detect_heading(text)

        # Split page into sentences first, then pack into chunks
        sentences = re.split(r"(?<=[.!?])\s+", text)

        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) > chunk_chars and current:
                chunks.append({
                    "content": current.strip(),
                    "page_number": page_number,
                    "section_heading": heading,
                    "chunk_index": chunk_index,
                    "token_count": _estimate_tokens(current),
                })
                chunk_index += 1
                # Start next chunk with overlap tail from the previous one
                current = current[-overlap_chars:] + " " + sentence if overlap_chars else sentence
            else:
                current = (current + " " + sentence).strip()

        if current.strip():
            chunks.append({
                "content": current.strip(),
                "page_number": page_number,
                "section_heading": heading,
                "chunk_index": chunk_index,
                "token_count": _estimate_tokens(current),
            })
            chunk_index += 1

    return chunks

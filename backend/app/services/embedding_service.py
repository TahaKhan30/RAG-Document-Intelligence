"""
Embedding service — generates vectors for text.

Designed behind a single interface so the provider can be swapped with a one-file
change. Currently uses Voyage AI (free tier: 200M tokens on voyage-3-lite).
To swap to OpenAI or a local sentence-transformers model, only this file changes.
"""
import voyageai
from app.core.config import settings

_client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)


async def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """
    Embed a batch of texts. input_type is "document" when indexing chunks,
    "query" when embedding a user's search question (Voyage optimizes each differently).
    """
    if not texts:
        return []
    result = _client.embed(
        texts,
        model=settings.EMBEDDING_MODEL,
        input_type=input_type,
    )
    return result.embeddings


async def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    embeddings = await embed_texts([text], input_type="query")
    return embeddings[0]

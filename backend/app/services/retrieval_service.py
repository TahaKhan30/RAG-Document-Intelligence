"""
Retrieval service — finds the most relevant chunks for a query.

Implements HYBRID SEARCH: combines semantic (vector) similarity with keyword
(full-text) matching, then merges with Reciprocal Rank Fusion (RRF). Pure vector
search misses exact keyword matches (e.g. searching "PTO policy" can miss a doc
titled "PTO Policy 2026"); hybrid search fixes this and measurably improves recall.

All queries are scoped by user_id in the WHERE clause for multi-tenant isolation.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding_service import embed_query
from app.core.config import settings

# RRF constant — standard value from the literature
RRF_K = 60


async def hybrid_search(
    db: AsyncSession,
    user_id: int,
    query: str,
    document_id: int | None = None,
    top_k: int | None = None,
) -> list[dict]:
    """
    Returns the top_k most relevant chunks as list of dicts with content + citation metadata.
    If document_id is given, search is scoped to that document. Otherwise searches all
    the user's documents (cross-document search).
    """
    top_k = top_k or settings.TOP_K
    query_embedding = await embed_query(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    doc_filter = "AND c.document_id = :document_id" if document_id else ""

    # Vector search — cosine distance, lower is closer
    vector_sql = text(f"""
        SELECT c.id, c.content, c.page_number, c.section_heading, c.document_id,
               d.title AS document_title,
               ROW_NUMBER() OVER (ORDER BY c.embedding <=> :embedding) AS rank
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.user_id = :user_id {doc_filter}
        ORDER BY c.embedding <=> :embedding
        LIMIT 20
    """)

    # Keyword search — PostgreSQL full-text search
    keyword_sql = text(f"""
        SELECT c.id, c.content, c.page_number, c.section_heading, c.document_id,
               d.title AS document_title,
               ROW_NUMBER() OVER (
                 ORDER BY ts_rank(to_tsvector('english', c.content),
                                  plainto_tsquery('english', :query)) DESC
               ) AS rank
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.user_id = :user_id {doc_filter}
          AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
        LIMIT 20
    """)

    params = {"embedding": embedding_str, "user_id": user_id, "query": query}
    if document_id:
        params["document_id"] = document_id

    vector_rows = (await db.execute(vector_sql, params)).mappings().all()
    keyword_rows = (await db.execute(keyword_sql, params)).mappings().all()

    # Reciprocal Rank Fusion — merge the two ranked lists
    scores: dict[int, float] = {}
    chunk_data: dict[int, dict] = {}

    for row in vector_rows:
        cid = row["id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (RRF_K + row["rank"])
        chunk_data[cid] = dict(row)

    for row in keyword_rows:
        cid = row["id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (RRF_K + row["rank"])
        chunk_data[cid] = dict(row)

    ranked_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:top_k]

    return [
        {
            "chunk_id": cid,
            "content": chunk_data[cid]["content"],
            "page_number": chunk_data[cid]["page_number"],
            "section_heading": chunk_data[cid]["section_heading"],
            "document_id": chunk_data[cid]["document_id"],
            "document_title": chunk_data[cid]["document_title"],
        }
        for cid in ranked_ids
    ]

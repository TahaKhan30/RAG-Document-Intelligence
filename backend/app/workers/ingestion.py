"""
Ingestion pipeline — runs in the background after upload.

Flow: extract text → chunk → embed → store, updating document.status at each stage
so the frontend can show live progress. Any failure sets status='failed' with the
error message rather than crashing silently.
"""
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.pdf_service import extract_pages, count_words
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import embed_texts


async def _set_status(db, document_id: int, status: str, **fields):
    await db.execute(
        update(Document).where(Document.id == document_id).values(status=status, **fields)
    )
    await db.commit()


async def process_document(document_id: int, pdf_bytes: bytes):
    """Full ingestion pipeline. Called as a FastAPI BackgroundTask."""
    async with AsyncSessionLocal() as db:
        try:
            # 1. Extract text page by page
            await _set_status(db, document_id, "extracting")
            pages = extract_pages(pdf_bytes)
            words = count_words(pages)

            await db.execute(
                update(Document).where(Document.id == document_id).values(
                    page_count=len(pages), word_count=words
                )
            )
            await db.commit()

            # 2. Chunk
            await _set_status(db, document_id, "chunking")
            chunk_dicts = chunk_pages(pages)

            if not chunk_dicts:
                await _set_status(db, document_id, "failed", error_message="No chunks produced from document.")
                return

            # 3. Embed (batch)
            await _set_status(db, document_id, "embedding")

            # Get user_id for denormalization onto chunks
            doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one()
            user_id = doc.user_id

            texts = [c["content"] for c in chunk_dicts]

            # Embed in batches of 100 to stay within API limits
            all_embeddings = []
            for i in range(0, len(texts), 100):
                batch = texts[i:i + 100]
                embeddings = await embed_texts(batch, input_type="document")
                all_embeddings.extend(embeddings)

            # 4. Store chunks with embeddings
            for c, embedding in zip(chunk_dicts, all_embeddings):
                db.add(Chunk(
                    document_id=document_id,
                    user_id=user_id,
                    content=c["content"],
                    embedding=embedding,
                    page_number=c["page_number"],
                    section_heading=c["section_heading"],
                    chunk_index=c["chunk_index"],
                    token_count=c["token_count"],
                ))
            await db.commit()

            # 5. Mark ready
            await _set_status(
                db, document_id, "ready",
                chunk_count=len(chunk_dicts),
                indexed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            await _set_status(db, document_id, "failed", error_message=str(e)[:500])

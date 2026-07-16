from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.config import settings


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Denormalized user_id — lets us filter by owner in the WHERE clause of vector
    # queries without a join. Recommended by production RAG guides for multi-tenant filtering.
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # The embedding vector — dimension matches the embedding model (voyage-3-lite = 512)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIM))

    # Citation metadata — enables "answer from page 4, section 2"
    page_number: Mapped[int] = mapped_column(Integer, default=0)
    section_heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

    document: Mapped["Document"] = relationship(back_populates="chunks")  # noqa: F821

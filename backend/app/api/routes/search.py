from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.retrieval_service import hybrid_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cross-document hybrid search across all the user's documents."""
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = await hybrid_search(db, user.id, body.query, document_id=None, top_k=10)
    return {"results": results}

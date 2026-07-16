from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.schemas.chat import AskRequest, AnswerResponse, ConversationMessage
from app.services.rag_service import answer_question

router = APIRouter(prefix="/api/documents/{document_id}/chat", tags=["chat"])


async def _verify_doc(db, document_id, user_id):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=400, detail="Document is still processing.")
    return doc


@router.post("", response_model=AnswerResponse)
async def ask(
    document_id: int,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _verify_doc(db, document_id, user.id)

    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Save the user's question
    db.add(Conversation(document_id=document_id, user_id=user.id, role="user", content=body.question))
    await db.commit()

    # Generate the answer via RAG
    result = await answer_question(db, user.id, body.question, document_id=document_id)

    # Save the assistant's answer with cited chunks
    db.add(Conversation(
        document_id=document_id, user_id=user.id, role="assistant",
        content=result["answer"], cited_chunks=result["cited_chunks"],
    ))
    await db.commit()

    return result


@router.get("", response_model=list[ConversationMessage])
async def get_history(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _verify_doc(db, document_id, user.id)
    result = await db.execute(
        select(Conversation)
        .where(Conversation.document_id == document_id, Conversation.user_id == user.id)
        .order_by(asc(Conversation.created_at))
    )
    return result.scalars().all()

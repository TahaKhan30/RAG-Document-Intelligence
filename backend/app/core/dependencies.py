from fastapi import Depends, HTTPException, Cookie
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.jwt_service import decode_access_token


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias=settings.ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — use on any protected endpoint:

        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            ...

    Reads the HttpOnly cookie automatically — no Authorization header needed.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(access_token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

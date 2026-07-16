import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.core.cookies import set_auth_cookies, clear_auth_cookies
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, MessageResponse
from app.services.password_service import hash_password, verify_password
from app.services.jwt_service import create_access_token, create_refresh_token, decode_refresh_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_token(token: str) -> str:
    """Store only the hash of the refresh token in DB — never the raw value."""
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Log the user in immediately after registration
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    await _save_refresh_token(db, user.id, refresh_token)
    set_auth_cookies(response, access_token, refresh_token)

    return user


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    await _save_refresh_token(db, user.id, refresh_token)

    # FastAPI sets the cookies — frontend never handles tokens directly
    set_auth_cookies(response, access_token, refresh_token)

    return user


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = decode_refresh_token(refresh_token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check token exists in DB and is not revoked
    token_hash = _hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    # Revoke old refresh token (rotation — each token can only be used once)
    stored.revoked = True
    await db.commit()

    # Fetch user and issue new token pair
    user_result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token(user.id)
    await _save_refresh_token(db, user.id, new_refresh)
    set_auth_cookies(response, new_access, new_refresh)

    return {"message": "Tokens refreshed"}


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    # Revoke the refresh token in DB if present
    if refresh_token:
        token_hash = _hash_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.revoked = True
            await db.commit()

    # Always clear cookies — even if token not found
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Returns the currently authenticated user. Use Depends(get_current_user) on any protected route."""
    return user


# ── internal helper ──────────────────────────────────────────────────────────

async def _save_refresh_token(db: AsyncSession, user_id: int, raw_token: str) -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        token_hash=_hash_token(raw_token),
        user_id=user_id,
        expires_at=expires,
    ))
    await db.commit()

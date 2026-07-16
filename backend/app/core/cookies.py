from fastapi import Response
from app.core.config import settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set both auth cookies on the response. Called only by FastAPI — never by frontend."""

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,                                        # JS cannot read this
        secure=True,                                          # HTTPS only (set False for local dev)
        samesite="lax",                                       # lax = safe for most SPAs; strict = stricter
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",                                     # narrower path — only sent to refresh endpoint
    )


def clear_auth_cookies(response: Response) -> None:
    """Expire both cookies immediately. Called on logout."""

    response.delete_cookie(key=settings.ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(key=settings.REFRESH_TOKEN_COOKIE, path="/api/auth")

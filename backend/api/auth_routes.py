# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# auth_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Authentication API routes."""

from fastapi import APIRouter, Response, Cookie
from typing import Optional

from ..models import LoginRequest, LoginResponse
from ..config import get_settings
from ..auth import (
    verify_credentials,
    create_session,
    delete_session,
    get_session_user,
    SESSION_COOKIE_NAME,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response) -> LoginResponse:
    """Authenticate user and create session."""
    if verify_credentials(request.username, request.password):
        token = create_session(request.username)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
        )
        return LoginResponse(success=True, message="Login successful")

    return LoginResponse(success=False, message="Invalid credentials")


@router.post("/logout")
async def logout(
    response: Response,
    session: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> dict:
    """Log out and delete session."""
    if session:
        delete_session(session)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"success": True}


@router.get("/check")
async def check_auth(
    session: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> dict:
    """Check if user is authenticated."""
    settings = get_settings()

    # Bypass authentication if configured
    if settings.bypass_auth:
        return {"authenticated": True}

    if session and get_session_user(session):
        return {"authenticated": True}
    return {"authenticated": False}

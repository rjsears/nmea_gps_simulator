# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# auth.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Authentication module."""

import secrets
from typing import Optional
from fastapi import Cookie, HTTPException, status

from .config import get_settings

SESSION_COOKIE_NAME = "gps_session"

# In-memory session store (sessions expire on container restart)
_sessions: dict[str, str] = {}


def verify_credentials(username: str, password: str) -> bool:
    """Verify username and password against configured credentials.

    Args:
        username: Provided username
        password: Provided password

    Returns:
        True if credentials match
    """
    settings = get_settings()
    return username == settings.username and password == settings.password


def create_session(username: str) -> str:
    """Create a new session for the user.

    Args:
        username: Username to associate with session

    Returns:
        Session token
    """
    token = secrets.token_urlsafe(32)
    _sessions[token] = username
    return token


def delete_session(token: str) -> None:
    """Delete a session.

    Args:
        token: Session token to delete
    """
    _sessions.pop(token, None)


def get_session_user(token: str) -> Optional[str]:
    """Get username for session token.

    Args:
        token: Session token

    Returns:
        Username or None if invalid
    """
    return _sessions.get(token)


async def get_current_user(
    session: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> str:
    """FastAPI dependency to get current authenticated user.

    Args:
        session: Session cookie value

    Returns:
        Username

    Raises:
        HTTPException: If not authenticated
    """
    settings = get_settings()

    # Bypass authentication if configured
    if settings.bypass_auth:
        return "bypass_user"

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    username = get_session_user(session)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    return username

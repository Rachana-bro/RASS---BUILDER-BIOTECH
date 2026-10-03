"""
RASS-BUILDER: Stage 9 FastAPI Security Dependencies
Implements token resolution, user context injection, role verification,
and unauthorized/forbidden access enforcement.
"""

import os
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserRole, AccountStatus
from .repository import user_repository, SqliteUserRepository


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """
    Resolves the authenticated user from the Bearer token if provided.
    - If an invalid or expired token is passed: raises HTTP 401.
    - If account is suspended: raises HTTP 403.
    - If strict auth mode is enabled and no token is passed: raises HTTP 401.
    - Otherwise, returns User entity or None for legacy/backward-compatible requests.
    """
    token: Optional[str] = None

    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Check raw Authorization header fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if token:
        resolved = user_repository.get_session(token)
        if not resolved:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session token has expired or is invalid. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        session, user = resolved

        if user.account_status == AccountStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is suspended. Access denied.",
            )

        return user

    # Strict auth check
    strict_auth_env = os.environ.get("RASS_REQUIRE_AUTH") == "1"
    strict_auth_header = request.headers.get("X-Require-Auth") == "true"

    if strict_auth_env or strict_auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return None


def require_authenticated_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """
    Strict dependency requiring a valid authenticated user session.
    Returns HTTP 401 if unauthenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin_user(
    user: User = Depends(require_authenticated_user),
) -> User:
    """
    Role-based dependency enforcing ADMIN privileges.
    Returns HTTP 403 if the user does not possess the ADMIN role.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges are required for this action.",
        )
    return user

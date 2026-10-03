"""
RASS-BUILDER: Stage 9 Authentication & Access Control Package
Provides user models, secure PBKDF2 hashing, session management,
and role-based access control (USER / ADMIN).
"""

from .models import User, UserRole, AccountStatus, Session
from .security import hash_password, verify_password, generate_token
from .repository import SqliteUserRepository, user_repository
from .dependencies import (
    get_current_user_optional,
    require_authenticated_user,
    require_admin_user,
)

__all__ = [
    "User",
    "UserRole",
    "AccountStatus",
    "Session",
    "hash_password",
    "verify_password",
    "generate_token",
    "SqliteUserRepository",
    "user_repository",
    "get_current_user_optional",
    "require_authenticated_user",
    "require_admin_user",
]

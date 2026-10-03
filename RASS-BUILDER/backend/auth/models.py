"""
RASS-BUILDER: Stage 9 Authentication Models & Schemas
Defines domain User & Session entities, role designations, and API contracts.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


@dataclass
class User:
    """
    Internal domain entity representing an authenticated RASS-BUILDER user.
    Passwords are NEVER stored in plaintext.
    """
    user_id: str
    name: str
    email: str
    password_hash: str
    salt: str
    role: UserRole = UserRole.USER
    account_status: AccountStatus = AccountStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Safe public representation strictly excluding password_hash and salt."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, UserRole) else str(self.role),
            "account_status": self.account_status.value if isinstance(self.account_status, AccountStatus) else str(self.account_status),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Session:
    """Represents an active authenticated session token."""
    session_id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


# ==============================================================================
# PYDANTIC SCHEMAS FOR API REQUESTS & RESPONSES
# ==============================================================================

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name or display name")
    email: str = Field(..., min_length=3, max_length=150, description="Email address or username")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="Requested role (default USER)")


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150, description="Email or username")
    password: str = Field(..., min_length=1, max_length=128, description="Password")


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    account_status: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class SessionStatusResponse(BaseModel):
    is_authenticated: bool
    user: Optional[UserResponse] = None


class AdminUserSummary(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    account_status: str
    created_at: str
    jobs_count: int = 0

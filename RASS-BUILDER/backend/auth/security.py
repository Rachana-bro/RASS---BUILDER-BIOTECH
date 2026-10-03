"""
RASS-BUILDER: Stage 9 Cryptographic Security & Password Hashing
Implements PBKDF2 HMAC SHA-256 password hashing with unique per-user cryptographic salts,
constant-time digest comparison, and cryptographically secure session token generation.
Compatible across Windows, Linux, and macOS without binary C-extension dependencies.
"""

import hashlib
import hmac
import secrets
import re
from typing import Tuple, Optional


HASH_ALGORITHM = "sha256"
ITERATIONS = 100_000
SALT_BYTES = 16


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hashes a password with PBKDF2 HMAC SHA-256 using a cryptographic salt.
    Returns: (password_hash, salt_hex)
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if not salt:
        salt = secrets.token_hex(SALT_BYTES)

    salt_bytes = salt.encode("utf-8")
    derived_key = hashlib.pbkdf2_hmac(
        hash_name=HASH_ALGORITHM,
        password=password.encode("utf-8"),
        salt=salt_bytes,
        iterations=ITERATIONS,
    )
    password_hash = derived_key.hex()
    return password_hash, salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """
    Validates candidate password against stored salt and hash in constant time
    to prevent timing attacks.
    """
    if not password or not salt or not password_hash:
        return False

    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def generate_token() -> str:
    """Generates a high-entropy URL-safe bearer token (256 bits)."""
    return secrets.token_urlsafe(32)


def generate_user_id() -> str:
    """Generates a structured, human-readable user ID."""
    return f"USR-{secrets.token_hex(4).upper()}"


def generate_session_id() -> str:
    """Generates a unique session identifier."""
    return f"SES-{secrets.token_hex(4).upper()}"


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validates password complexity requirements:
    - Minimum 8 characters
    - At least one letter
    - At least one numeric digit or special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."

    if not re.search(r"[0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one number or special character."

    return True, ""

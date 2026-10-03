"""
RASS-BUILDER: Stage 9 SQLite User & Session Repository
Provides database persistence for users and session tokens,
enforcing unique constraints, relational foreign keys, and atomic transactions.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any

from database.connection import get_db_connection, get_database_path
from database.schema import init_db
from .models import User, UserRole, AccountStatus, Session
from .security import generate_session_id, generate_token


class SqliteUserRepository:
    """
    Persistent SQLite storage layer for users and active login sessions.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_database_path()
        init_db(self.db_path)

    def save_user(self, user: User) -> User:
        """Upserts user into the SQLite database."""
        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO users (
                        user_id, name, email, password_hash, salt, role,
                        account_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        name = excluded.name,
                        email = excluded.email,
                        password_hash = excluded.password_hash,
                        salt = excluded.salt,
                        role = excluded.role,
                        account_status = excluded.account_status,
                        updated_at = excluded.updated_at;
                    """,
                    (
                        user.user_id,
                        user.name,
                        user.email.strip().lower(),
                        user.password_hash,
                        user.salt,
                        user.role.value if isinstance(user.role, UserRole) else str(user.role),
                        user.account_status.value if isinstance(user.account_status, AccountStatus) else str(user.account_status),
                        user.created_at.isoformat(),
                        user.updated_at.isoformat(),
                    ),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Looks up user by unique ID."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?;",
                (user_id,),
            ).fetchone()
            return self._row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Looks up user by email or username (case-insensitive)."""
        clean_email = email.strip().lower()
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = ?;",
                (clean_email,),
            ).fetchone()
            return self._row_to_user(row) if row else None

    def list_users(self, limit: int = 100) -> List[User]:
        """Returns registered users sorted by creation date."""
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at ASC LIMIT ?;",
                (limit,),
            ).fetchall()
            return [self._row_to_user(r) for r in rows]

    def count_user_jobs(self, user_id: str) -> int:
        """Counts jobs associated with a specific user."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE user_id = ?;",
                (user_id,),
            ).fetchone()
            return row["c"] if row else 0

    def create_session(
        self,
        user_id: str,
        duration_seconds: int = 86400,
    ) -> Session:
        """
        Issues a new cryptographically secure session token with expiration.
        Default TTL: 24 hours.
        """
        session_id = generate_session_id()
        token = generate_token()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=duration_seconds)

        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO sessions (
                        session_id, user_id, token, created_at, expires_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, 1);
                    """,
                    (
                        session_id,
                        user_id,
                        token,
                        now.isoformat(),
                        expires_at.isoformat(),
                    ),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        return Session(
            session_id=session_id,
            user_id=user_id,
            token=token,
            created_at=now,
            expires_at=expires_at,
            is_active=True,
        )

    def get_session(self, token: str) -> Optional[Tuple[Session, User]]:
        """
        Validates token and returns linked active Session and User.
        If expired, automatically marks session inactive.
        """
        if not token:
            return None

        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT s.session_id, s.user_id, s.token, s.created_at, s.expires_at, s.is_active,
                       u.name, u.email, u.password_hash, u.salt, u.role, u.account_status,
                       u.created_at as u_created_at, u.updated_at as u_updated_at
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.token = ?;
                """,
                (token,),
            ).fetchone()

            if not row or not bool(row["is_active"]):
                return None

            expires_at = datetime.fromisoformat(row["expires_at"])
            now = datetime.now(timezone.utc)

            # Check expiration
            if now >= expires_at:
                conn.execute(
                    "UPDATE sessions SET is_active = 0 WHERE token = ?;",
                    (token,),
                )
                return None

            session = Session(
                session_id=row["session_id"],
                user_id=row["user_id"],
                token=row["token"],
                created_at=datetime.fromisoformat(row["created_at"]),
                expires_at=expires_at,
                is_active=True,
            )

            user = User(
                user_id=row["user_id"],
                name=row["name"],
                email=row["email"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                role=UserRole(row["role"]),
                account_status=AccountStatus(row["account_status"]),
                created_at=datetime.fromisoformat(row["u_created_at"]),
                updated_at=datetime.fromisoformat(row["u_updated_at"]),
            )

            return session, user

    def invalidate_session(self, token: str) -> bool:
        """Revokes an active session token upon logout."""
        if not token:
            return False

        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                cur = conn.execute(
                    "UPDATE sessions SET is_active = 0 WHERE token = ? AND is_active = 1;",
                    (token,),
                )
                modified = cur.rowcount > 0
                conn.execute("COMMIT;")
                return modified
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Revokes all active sessions for a user."""
        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                cur = conn.execute(
                    "UPDATE sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1;",
                    (user_id,),
                )
                count = cur.rowcount
                conn.execute("COMMIT;")
                return count
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def clear(self) -> None:
        """Empties users and sessions (used for test isolation)."""
        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute("DELETE FROM sessions;")
                # Unlink any jobs referencing users so foreign key constraint is satisfied
                conn.execute("UPDATE jobs SET user_id = NULL;")
                conn.execute("DELETE FROM users;")
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise


    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Maps an SQLite row to a User domain entity."""
        return User(
            user_id=row["user_id"],
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            role=UserRole(row["role"]),
            account_status=AccountStatus(row["account_status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# Global singleton instance
user_repository = SqliteUserRepository()

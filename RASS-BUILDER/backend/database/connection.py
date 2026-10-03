"""
RASS-BUILDER: Stage 8 Database Connection Manager
Manages SQLite database connections, Write-Ahead Logging (WAL) configuration,
and foreign-key enforcement for reliable persistence.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional


# Default to backend/data/rass_builder.db or environment variable override
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "rass_builder.db"


def get_database_path() -> Path:
    """Resolves active database path from environment or default location."""
    env_path = os.environ.get("RASS_DB_PATH") or os.environ.get("DATABASE_PATH")
    if env_path:
        return Path(env_path)
    # Ensure directory exists
    DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB_PATH


@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing configured SQLite database connection.
    Enforces foreign-key constraints and WAL mode for high concurrent throughput.
    """
    path = db_path or get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(path),
        timeout=10.0,
        check_same_thread=False,
        isolation_level=None,  # Autocommit mode; transactions managed via BEGIN/COMMIT
    )
    conn.row_factory = sqlite3.Row

    try:
        # Enforce foreign key constraints and WAL concurrency mode
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 10000;")
        yield conn
    finally:
        conn.close()

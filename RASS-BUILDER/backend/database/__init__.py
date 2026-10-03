"""
RASS-BUILDER: Stage 8 Database Module
Exports connection management, schema initialization, and SQLite repository.
"""

from .connection import get_db_connection, get_database_path
from .schema import init_db, CURRENT_SCHEMA_VERSION
from .repository import SqliteJobRepository

__all__ = [
    "get_db_connection",
    "get_database_path",
    "init_db",
    "CURRENT_SCHEMA_VERSION",
    "SqliteJobRepository",
]

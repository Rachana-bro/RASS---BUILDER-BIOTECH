"""
RASS-BUILDER: Deterministic Database Initialization Script
Initializes SQLite relational schema, creates tables, indexes, and version metadata idempotently.
Safe to run on new installations or existing deployments (preserves existing data).

Usage:
    python backend/scripts/init_db.py
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database.schema import init_db
from database.connection import get_database_path


def main():
    db_path = get_database_path()
    print(f"[*] Initializing RASS-BUILDER database at: {db_path}")
    init_db(db_path)
    print("[+] Database schema, tables, and indexes initialized successfully.")


if __name__ == "__main__":
    main()

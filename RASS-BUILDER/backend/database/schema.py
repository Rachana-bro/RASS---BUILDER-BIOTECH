"""
RASS-BUILDER: Stage 8 Database Schema & Initialization
Defines relational tables, foreign key constraints, indexes, and versioned migrations.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from .connection import get_db_connection, get_database_path


CURRENT_SCHEMA_VERSION = 1


SCHEMA_V1_SQL = """
-- 1. Schema version tracker
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

-- 2. Asynchronous genomic analysis jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    message TEXT NOT NULL,
    input_metadata TEXT NOT NULL DEFAULT '{}',
    raw_sequence TEXT,
    file_path TEXT,
    error TEXT,
    idempotency_key TEXT,
    cancelled INTEGER NOT NULL DEFAULT 0,
    user_id TEXT
);

-- 3. Structured Stage 5 / Stage 6 analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    result_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,
    sequence_metadata TEXT NOT NULL DEFAULT '{}',
    model_metadata TEXT NOT NULL DEFAULT '{}',
    embedding_metadata TEXT NOT NULL DEFAULT '{}',
    pattern_results TEXT NOT NULL DEFAULT '[]',
    variant_results TEXT NOT NULL DEFAULT '[]',
    confidence REAL,
    analysis_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    raw_result TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

-- 4. Stage 9 Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER',
    account_status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 5. Stage 9 Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 6. Stage 10 Audit Logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    user_id TEXT,
    request_id TEXT,
    status TEXT NOT NULL,
    ip_address TEXT,
    details TEXT NOT NULL DEFAULT '{}'
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_results_job_id ON analysis_results(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_logs(request_id);
"""



def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initializes database schema idempotently.
    Ensures tables, indexes, and version metadata exist without altering existing records.
    Applies migrations for pre-existing databases safely.
    """
    target_path = db_path or get_database_path()
    with get_db_connection(target_path) as conn:
        # 1. Execute schema definition
        conn.executescript(SCHEMA_V1_SQL)

        # 2. Migration: Ensure user_id column exists on pre-existing jobs tables
        job_cols = [
            col["name"]
            for col in conn.execute("PRAGMA table_info(jobs);").fetchall()
        ]
        if "user_id" not in job_cols:
            conn.execute(
                "ALTER TABLE jobs ADD COLUMN user_id TEXT REFERENCES users(user_id);"
            )

        # 3. Register schema version 1 tracking
        row = conn.execute(
            "SELECT version FROM schema_versions WHERE version = ?;",
            (CURRENT_SCHEMA_VERSION,),
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT OR IGNORE INTO schema_versions (version, applied_at, description) VALUES (?, ?, ?);",
                (
                    CURRENT_SCHEMA_VERSION,
                    datetime.now(timezone.utc).isoformat(),
                    "Stage 8 & Stage 9 Schema: jobs, analysis_results, users, sessions, and indexes",
                ),
            )


if __name__ == "__main__":
    init_db()
    print("RASS-BUILDER: Database schema initialized successfully.")




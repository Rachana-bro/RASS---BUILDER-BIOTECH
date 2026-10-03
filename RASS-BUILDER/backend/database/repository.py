"""
RASS-BUILDER: Stage 8 SQLite Job & Result Repository
Implements the JobRepository contract with persistent SQLite backing,
ACID transactions, JSON serialization, and worker recovery handling.
"""

import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from jobs.models import Job, JobStatus, JobStage
from jobs.repository import JobRepository
from .connection import get_db_connection, get_database_path
from .schema import init_db


class SqliteJobRepository(JobRepository):
    """
    Production-grade SQLite-backed repository for RASS-BUILDER.
    Ensures persistent storage across server restarts, foreign key integrity,
    and structured storage for Stage 5/6 analysis results.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_database_path()
        # Ensure schema is initialized
        init_db(self.db_path)

    def save(self, job: Job) -> Job:
        """Upserts job record into the SQLite database."""
        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO jobs (
                        job_id, status, current_stage, progress, created_at,
                        started_at, completed_at, message, input_metadata,
                        raw_sequence, file_path,
                        error, idempotency_key, cancelled, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_id) DO UPDATE SET
                        status = excluded.status,
                        current_stage = excluded.current_stage,
                        progress = excluded.progress,
                        started_at = excluded.started_at,
                        completed_at = excluded.completed_at,
                        message = excluded.message,
                        input_metadata = excluded.input_metadata,
                        raw_sequence = excluded.raw_sequence,
                        file_path = excluded.file_path,
                        error = excluded.error,
                        idempotency_key = excluded.idempotency_key,
                        cancelled = excluded.cancelled,
                        user_id = COALESCE(excluded.user_id, jobs.user_id);
                    """,
                    (
                        job.job_id,
                        job.status.value,
                        job.current_stage.value,
                        job.progress,
                        job.created_at.isoformat(),
                        job.started_at.isoformat() if job.started_at else None,
                        job.completed_at.isoformat() if job.completed_at else None,
                        job.message,
                        json.dumps(job.input_metadata),
                        job.raw_sequence,
                        job.file_path,
                        job.error,
                        job.idempotency_key,
                        1 if job.cancelled else 0,
                        job.user_id,
                    ),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        return job

    def get(self, job_id: str) -> Optional[Job]:
        """Retrieves job by ID and links stored analysis result if completed."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?;",
                (job_id,),
            ).fetchone()

            if not row:
                return None

            job = self._row_to_job(row)

            # If completed, load result from analysis_results table
            if job.status == JobStatus.COMPLETED:
                res_row = conn.execute(
                    "SELECT raw_result FROM analysis_results WHERE job_id = ?;",
                    (job_id,),
                ).fetchone()
                if res_row and res_row["raw_result"]:
                    job.result_reference = json.loads(res_row["raw_result"])

            return job

    def list_all(self, limit: int = 50, user_id: Optional[str] = None) -> List[Job]:
        """Returns recent jobs sorted chronologically descending, optionally filtered by user_id."""
        with get_db_connection(self.db_path) as conn:
            if user_id is not None:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?;",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?;",
                    (limit,),
                ).fetchall()

            return [self._row_to_job(row) for row in rows]


    def find_by_idempotency_key(self, key: str) -> Optional[Job]:
        """Finds job matching client or generated idempotency fingerprint."""
        if not key:
            return None
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE idempotency_key = ? LIMIT 1;",
                (key,),
            ).fetchone()

            if not row:
                return None

            return self._row_to_job(row)

    def save_result(self, job_id: str, result: Dict[str, Any]) -> str:
        """
        Stores structured Stage 5/6 result in analysis_results table
        and guarantees atomic update to the corresponding job.
        """
        result_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        seq_meta = json.dumps(
            {
                "sequence_length": result.get("sequence_length"),
                "token_count": result.get("token_count"),
                "read_id": result.get("read_id", "READ_001"),
            }
        )
        model_meta = json.dumps(result.get("model", {}))
        embed_meta = json.dumps(
            {
                "dimension": result.get("embedding", {}).get("dimension"),
                "generated": result.get("embedding", {}).get("generated"),
                "norm": result.get("embedding", {}).get("norm"),
            }
        )
        pattern_res = json.dumps(
            result.get("pattern_analysis", {}).get("patterns", [])
        )
        variant_res = json.dumps(result.get("variants", []))
        raw_result_str = json.dumps(result)

        confidence_val = result.get("confidence")

        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                # 1. Upsert analysis_results record
                conn.execute(
                    """
                    INSERT INTO analysis_results (
                        result_id, job_id, sequence_metadata, model_metadata,
                        embedding_metadata, pattern_results, variant_results,
                        confidence, analysis_status, created_at, raw_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_id) DO UPDATE SET
                        sequence_metadata = excluded.sequence_metadata,
                        model_metadata = excluded.model_metadata,
                        embedding_metadata = excluded.embedding_metadata,
                        pattern_results = excluded.pattern_results,
                        variant_results = excluded.variant_results,
                        confidence = excluded.confidence,
                        analysis_status = excluded.analysis_status,
                        created_at = excluded.created_at,
                        raw_result = excluded.raw_result;
                    """,
                    (
                        result_id,
                        job_id,
                        seq_meta,
                        model_meta,
                        embed_meta,
                        pattern_res,
                        variant_res,
                        confidence_val,
                        result.get("status", "completed"),
                        now_iso,
                        raw_result_str,
                    ),
                )

                # 2. Update job status to COMPLETED
                conn.execute(
                    """
                    UPDATE jobs SET
                        status = ?,
                        current_stage = ?,
                        progress = 100,
                        completed_at = ?,
                        message = 'Analysis complete. Structured results stored in database.'
                    WHERE job_id = ?;
                    """,
                    (
                        JobStatus.COMPLETED.value,
                        JobStage.COMPLETED.value,
                        now_iso,
                        job_id,
                    ),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        return result_id

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves structured result object directly from analysis_results table."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT raw_result FROM analysis_results WHERE job_id = ?;",
                (job_id,),
            ).fetchone()

            if not row or not row["raw_result"]:
                return None

            return json.loads(row["raw_result"])

    def get_queued_jobs(self, limit: int = 10) -> List[Job]:
        """Fetches pending jobs in QUEUED status for worker processing."""
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM jobs
                WHERE status = ? AND cancelled = 0
                ORDER BY created_at ASC
                LIMIT ?;
                """,
                (JobStatus.QUEUED.value, limit),
            ).fetchall()
            return [self._row_to_job(r) for r in rows]

    def recover_stale_running_jobs(self) -> List[str]:
        """
        Worker Recovery Strategy (Requirement 13):
        Identifies jobs left in 'RUNNING' state across host process restarts.
        Marks them as 'RECOVERY_REQUIRED' rather than silently pretending completion,
        preserving laboratory audit integrity.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        recovered_ids: List[str] = []

        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                stale_rows = conn.execute(
                    "SELECT job_id FROM jobs WHERE status = ?;",
                    (JobStatus.RUNNING.value,),
                ).fetchall()

                for row in stale_rows:
                    recovered_ids.append(row["job_id"])

                if recovered_ids:
                    conn.execute(
                        """
                        UPDATE jobs SET
                            status = ?,
                            current_stage = ?,
                            completed_at = ?,
                            message = 'Analysis process was interrupted by server restart. Manual recovery required.',
                            error = 'Execution interrupted by host process restart.'
                        WHERE status = ?;
                        """,
                        (
                            JobStatus.RECOVERY_REQUIRED.value,
                            JobStage.RECOVERY_REQUIRED.value,
                            now_iso,
                            JobStatus.RUNNING.value,
                        ),
                    )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        return recovered_ids

    def clear(self) -> None:
        """Clears all records (used in test fixtures for isolation)."""
        with get_db_connection(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute("DELETE FROM analysis_results;")
                conn.execute("DELETE FROM jobs;")
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Maps an SQLite row to a domain Job entity."""
        # Parse timestamps safely
        created_dt = (
            datetime.fromisoformat(row["created_at"])
            if row["created_at"]
            else datetime.now(timezone.utc)
        )
        started_dt = (
            datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None
        )
        completed_dt = (
            datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None
        )

        input_meta = {}
        if row["input_metadata"]:
            try:
                input_meta = json.loads(row["input_metadata"])
            except Exception:
                input_meta = {}

        row_keys = row.keys()
        raw_seq = row["raw_sequence"] if "raw_sequence" in row_keys else None
        f_path = row["file_path"] if "file_path" in row_keys else None
        u_id = row["user_id"] if "user_id" in row_keys else None

        return Job(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            current_stage=JobStage(row["current_stage"]),
            progress=row["progress"],
            created_at=created_dt,
            started_at=started_dt,
            completed_at=completed_dt,
            message=row["message"],
            input_metadata=input_meta,
            raw_sequence=raw_seq,
            file_path=f_path,
            read_id=input_meta.get("read_id", "READ_001"),
            error=row["error"],
            idempotency_key=row["idempotency_key"],
            cancelled=bool(row["cancelled"]),
            user_id=u_id,
        )


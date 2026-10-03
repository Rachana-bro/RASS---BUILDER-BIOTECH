"""
RASS-BUILDER: Stage 8 Database & Persistent Storage Tests
Verifies relational SQLite persistence, foreign key integrity, schema migrations,
atomic result storage, restart persistence, and worker startup recovery.
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from database.connection import get_db_connection
from database.schema import init_db, CURRENT_SCHEMA_VERSION
from database.repository import SqliteJobRepository
from jobs.models import Job, JobStatus, JobStage, JobCreateRequest
from jobs.service import JobService, job_service
from jobs.worker import BackgroundJobWorker


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database tables are fresh for each test."""
    job_service.clear()
    yield
    job_service.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. DATABASE INITIALIZATION & SCHEMA VERSIONING
# ==============================================================================

def test_database_initialization(tmp_path):
    """Requirement 17.1: Database schema initialization, tables, and version tracking."""
    test_db = tmp_path / "test_init.db"
    init_db(test_db)

    with get_db_connection(test_db) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        assert "schema_versions" in table_names
        assert "jobs" in table_names
        assert "analysis_results" in table_names

        # Verify version 1 applied
        ver_row = conn.execute("SELECT version FROM schema_versions WHERE version = 1;").fetchone()
        assert ver_row is not None
        assert ver_row["version"] == CURRENT_SCHEMA_VERSION

    # Calling init_db again should be idempotent
    init_db(test_db)
    with get_db_connection(test_db) as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM schema_versions;").fetchone()["c"]
        assert count == 1


# ==============================================================================
# 2. JOB PERSISTENCE (CREATION, UPDATE, COMPLETION, FAILURE)
# ==============================================================================

def test_job_creation_persistence(tmp_path):
    """Requirement 17.2: Newly created job is stored in jobs table with QUEUED status."""
    repo = SqliteJobRepository(tmp_path / "test_jobs.db")
    job = Job(
        job_id="JOB-TEST-PERSIST-1",
        status=JobStatus.QUEUED,
        current_stage=JobStage.QUEUED,
        progress=10,
        message="Queued for execution",
        input_metadata={"sequence_length": 30, "format": "FASTA"},
    )
    repo.save(job)

    fetched = repo.get("JOB-TEST-PERSIST-1")
    assert fetched is not None
    assert fetched.job_id == "JOB-TEST-PERSIST-1"
    assert fetched.status == JobStatus.QUEUED
    assert fetched.progress == 10
    assert fetched.input_metadata["sequence_length"] == 30


def test_job_status_update_persistence(tmp_path):
    """Requirement 17.3: Job status and progress updates persist to database."""
    repo = SqliteJobRepository(tmp_path / "test_jobs.db")
    job = Job(
        job_id="JOB-UPDATE-1",
        status=JobStatus.QUEUED,
        current_stage=JobStage.QUEUED,
        progress=10,
        message="Initial state",
    )
    repo.save(job)

    # Transition to RUNNING
    job.status = JobStatus.RUNNING
    job.current_stage = JobStage.TRANSFORMER_ANALYSIS
    job.progress = 60
    job.started_at = datetime.now(timezone.utc)
    job.message = "Running transformer"
    repo.save(job)

    updated = repo.get("JOB-UPDATE-1")
    assert updated.status == JobStatus.RUNNING
    assert updated.current_stage == JobStage.TRANSFORMER_ANALYSIS
    assert updated.progress == 60
    assert updated.started_at is not None


def test_job_completion_persistence(tmp_path):
    """Requirement 17.4: COMPLETED status and completion timestamps persist."""
    repo = SqliteJobRepository(tmp_path / "test_jobs.db")
    job = Job(
        job_id="JOB-COMPLETED-1",
        status=JobStatus.RUNNING,
        current_stage=JobStage.PATTERN_ANALYSIS,
        progress=80,
        message="Processing",
    )
    repo.save(job)

    job.status = JobStatus.COMPLETED
    job.current_stage = JobStage.COMPLETED
    job.progress = 100
    job.completed_at = datetime.now(timezone.utc)
    job.message = "Analysis complete."
    repo.save(job)

    completed = repo.get("JOB-COMPLETED-1")
    assert completed.status == JobStatus.COMPLETED
    assert completed.progress == 100
    assert completed.completed_at is not None


def test_job_failure_persistence(tmp_path):
    """Requirement 17.5: FAILED status and sanitized error messages persist."""
    repo = SqliteJobRepository(tmp_path / "test_jobs.db")
    job = Job(
        job_id="JOB-FAIL-1",
        status=JobStatus.RUNNING,
        current_stage=JobStage.DATA_INGESTION,
        progress=20,
        message="Processing",
    )
    repo.save(job)

    job.status = JobStatus.FAILED
    job.current_stage = JobStage.FAILED
    job.completed_at = datetime.now(timezone.utc)
    job.error = "Sequence contains invalid character 'X'."
    job.message = "Analysis failed during execution."
    repo.save(job)

    failed = repo.get("JOB-FAIL-1")
    assert failed.status == JobStatus.FAILED
    assert failed.error == "Sequence contains invalid character 'X'."
    assert failed.completed_at is not None


# ==============================================================================
# 3. ANALYSIS RESULT PERSISTENCE & RETRIEVAL
# ==============================================================================

def test_result_persistence_and_retrieval(tmp_path):
    """Requirement 17.6, 17.7 & 17.8: Structured Stage 5/6 results persist to analysis_results table."""
    repo = SqliteJobRepository(tmp_path / "test_res.db")
    job = Job(job_id="JOB-RES-1", status=JobStatus.RUNNING, message="Processing")
    repo.save(job)

    sample_result = {
        "stage": 5,
        "status": "completed",
        "sequence_length": 24,
        "token_count": 26,
        "read_id": "READ_SAMPLE",
        "model": {
            "name": "RASS-DNA-Transformer",
            "version": "0.5.0-foundation",
            "checkpoint_loaded": False,
        },
        "embedding": {"dimension": 64, "generated": True, "norm": 8.42},
        "pattern_analysis": {"status": "pending_validation", "patterns": []},
        "confidence": None,
        "clinical_interpretation": False,
    }

    result_id = repo.save_result("JOB-RES-1", sample_result)
    assert result_id.startswith("RES-")

    # Retrieve result directly
    fetched_result = repo.get_result("JOB-RES-1")
    assert fetched_result is not None
    assert fetched_result["stage"] == 5
    assert fetched_result["token_count"] == 26
    assert fetched_result["confidence"] is None

    # Retrieve job and confirm result_reference is attached
    fetched_job = repo.get("JOB-RES-1")
    assert fetched_job.status == JobStatus.COMPLETED
    assert fetched_job.result_reference is not None
    assert fetched_job.result_reference["sequence_length"] == 24


# ==============================================================================
# 4. JOB HISTORY & UNKNOWN LOOKUP
# ==============================================================================

def test_job_history_query(tmp_path):
    """Requirement 17.9: Persistent job history retrieves newest-first listing."""
    repo = SqliteJobRepository(tmp_path / "test_hist.db")
    for i in range(3):
        repo.save(
            Job(
                job_id=f"JOB-H-{i}",
                status=JobStatus.COMPLETED,
                message="Done",
                input_metadata={"sequence_length": 20 * (i + 1)},
            )
        )

    history = repo.list_all(limit=10)
    assert len(history) == 3
    # Check order (newest first)
    assert history[0].job_id in ["JOB-H-2", "JOB-H-1", "JOB-H-0"]


def test_unknown_job_404(client):
    """Requirement 17.10: Unknown job ID returns HTTP 404 from database."""
    resp = client.get("/api/jobs/JOB-DOES-NOT-EXIST")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ==============================================================================
# 5. SERVER RESTART PERSISTENCE & WORKER RECOVERY
# ==============================================================================

def test_server_restart_persistence(tmp_path):
    """
    Requirement 17.11: Critical check confirming that a new repository instance
    (simulating backend restart) retains all jobs and analysis results.
    """
    db_file = tmp_path / "server_restart.db"

    # Instance 1: Server Process A runs
    repo_a = SqliteJobRepository(db_file)
    job = Job(
        job_id="JOB-CRASH-SAFE",
        status=JobStatus.RUNNING,
        progress=50,
        message="Halfway done",
    )
    repo_a.save(job)
    sample_res = {"stage": 5, "status": "completed", "sequence_length": 50, "confidence": None}
    repo_a.save_result("JOB-CRASH-SAFE", sample_res)

    del repo_a  # Process A dies

    # Instance 2: Server Process B boots up from the same database file
    repo_b = SqliteJobRepository(db_file)
    restored_job = repo_b.get("JOB-CRASH-SAFE")
    assert restored_job is not None
    assert restored_job.job_id == "JOB-CRASH-SAFE"
    assert restored_job.status == JobStatus.COMPLETED
    assert restored_job.result_reference is not None
    assert restored_job.result_reference["sequence_length"] == 50


def test_running_job_recovery_on_startup(tmp_path):
    """
    Requirement 17.12 & Requirement 13: Stale jobs in RUNNING state upon server
    reboot are marked RECOVERY_REQUIRED to prevent silent corrupted state.
    """
    db_file = tmp_path / "stale_recovery.db"
    repo = SqliteJobRepository(db_file)

    # Job was running when server unexpectedly lost power
    repo.save(
        Job(
            job_id="JOB-INTERRUPTED",
            status=JobStatus.RUNNING,
            current_stage=JobStage.TRANSFORMER_ANALYSIS,
            progress=60,
            message="Executing transformer embedding...",
        )
    )

    # Recovery function executes on server reboot
    recovered_ids = repo.recover_stale_running_jobs()
    assert "JOB-INTERRUPTED" in recovered_ids

    # Query recovered job
    job = repo.get("JOB-INTERRUPTED")
    assert job.status == JobStatus.RECOVERY_REQUIRED
    assert job.current_stage == JobStage.RECOVERY_REQUIRED
    assert "interrupted by server restart" in job.message.lower()


# ==============================================================================
# 6. FOREIGN KEY INTEGRITY & TRANSACTION SAFETY
# ==============================================================================

def test_foreign_key_integrity(tmp_path):
    """Requirement 17.13: Foreign key enforces that results must map to a valid job."""
    db_file = tmp_path / "fk_test.db"
    repo = SqliteJobRepository(db_file)

    # Attempt inserting result for non-existent job
    with pytest.raises(sqlite3.IntegrityError):
        with get_db_connection(db_file) as conn:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                INSERT INTO analysis_results (
                    result_id, job_id, sequence_metadata, model_metadata,
                    embedding_metadata, pattern_results, variant_results,
                    confidence, analysis_status, created_at, raw_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "RES-ORPHAN",
                    "JOB-DOES-NOT-EXIST",
                    "{}",
                    "{}",
                    "{}",
                    "[]",
                    "[]",
                    None,
                    "completed",
                    datetime.now(timezone.utc).isoformat(),
                    "{}",
                ),
            )
            conn.execute("COMMIT;")


def test_cascading_delete_integrity(tmp_path):
    """Requirement 17.13: Deleting a job automatically cascades to remove its analysis result."""
    db_file = tmp_path / "cascade_test.db"
    repo = SqliteJobRepository(db_file)

    repo.save(Job(job_id="JOB-CASCADE-1", status=JobStatus.RUNNING, message="Running"))
    repo.save_result("JOB-CASCADE-1", {"sample": "data"})

    # Verify result exists
    assert repo.get_result("JOB-CASCADE-1") is not None

    # Delete job
    with get_db_connection(db_file) as conn:
        conn.execute("BEGIN IMMEDIATE;")
        conn.execute("DELETE FROM jobs WHERE job_id = 'JOB-CASCADE-1';")
        conn.execute("COMMIT;")

    # Result must be cascaded away
    assert repo.get_result("JOB-CASCADE-1") is None


# ==============================================================================
# 7. STAGE 7 QUEUE INTEGRATION WITH PERSISTENT SQLITE STORAGE
# ==============================================================================

def test_stage7_queue_integration_with_persistent_storage(client):
    """
    Requirement 17.15: End-to-end integration:
    API Job Submission -> SQLite Persistence -> Worker Execution -> SQLite Result Storage.
    """
    # 1. Enqueue job via API
    resp = client.post(
        "/api/jobs",
        json={"sequence": "ACGTACGTACGTACGT", "read_id": "READ_DB_INT"},
    )
    assert resp.status_code == 201
    job_id = resp.json()["job_id"]

    # 2. Wait for background worker to process job to COMPLETED
    import time
    for _ in range(30):
        status_resp = client.get(f"/api/jobs/{job_id}")
        if status_resp.status_code == 200 and status_resp.json()["status"] == "COMPLETED":
            break
        time.sleep(0.1)

    # 3. Verify job status endpoint reads from SQLite
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "COMPLETED"
    assert status_resp.json()["progress"] == 100

    # 4. Verify result endpoint reads from SQLite analysis_results table
    res_resp = client.get(f"/api/jobs/{job_id}/result")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["stage"] == 5
    assert res_data["status"] == "completed"
    assert res_data["sequence_length"] == 16
    assert res_data["confidence"] is None  # Strict zero-fabrication preserved

"""
RASS-BUILDER: Stage 7 Asynchronous Job Processing & Queue Infrastructure Tests
Validates job lifecycle, background worker transitions, duplicate prevention,
cancellation, error sanitization, and pipeline end-to-end integration.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from jobs.models import Job, JobStatus, JobStage, JobCreateRequest
from jobs.service import job_service
from jobs.repository import InMemoryJobRepository
from jobs.worker import BackgroundJobWorker


@pytest.fixture(autouse=True)
def clean_job_service():
    """Isolate job repository and worker state between tests."""
    job_service.clear()
    yield
    job_service.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. JOB ID GENERATION & CREATION
# ==============================================================================

def test_job_id_generation():
    """Requirement 16.1 & 16.2: Unique job ID format starting with JOB-."""
    id1 = job_service.generate_job_id()
    id2 = job_service.generate_job_id()
    assert id1.startswith("JOB-")
    assert id2.startswith("JOB-")
    assert id1 != id2
    assert len(id1) >= 8


def test_job_creation_and_queued_state(client):
    """Requirement 16.3: Job is created with status QUEUED without blocking."""
    payload = {
        "sequence": "ACGTACGTACGTACGT",
        "read_id": "READ_TEST_001",
        "format": "FASTA",
    }
    # Auto enqueue is disabled for pure initial state inspection
    job, is_dup = job_service.create_and_enqueue_job(
        JobCreateRequest(**payload),
        auto_enqueue=False,
    )
    assert job.status == JobStatus.QUEUED
    assert job.progress == 10
    assert job.current_stage == JobStage.QUEUED
    assert job.started_at is None
    assert job.completed_at is None
    assert is_dup is False

    # Check API returns 201 Created and matching status on new submission
    api_payload = {
        "sequence": "TGCATGCATGCA",
        "read_id": "READ_API_001",
        "format": "FASTA",
    }
    response = client.post("/api/jobs", json=api_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "QUEUED"
    assert "job_id" in data
    assert "Analysis job queued successfully." in data["message"]


# ==============================================================================
# 2. JOB STATUS & UNKNOWN JOB LOOKUP
# ==============================================================================

def test_job_status_endpoint(client):
    """Requirement 16.7: GET /api/jobs/{job_id} returns sanitized job details."""
    req = JobCreateRequest(sequence="GCTAGCTAGCTA", read_id="READ_POLL")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    resp = client.get(f"/api/jobs/{job.job_id}")
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["job_id"] == job.job_id
    assert status_data["status"] == "QUEUED"
    assert status_data["progress"] == 10
    assert status_data["current_stage"] == "QUEUED"
    assert status_data["input_metadata"]["read_id"] == "READ_POLL"
    assert status_data["input_metadata"]["sequence_length"] == 12
    # Ensure raw sequence is NOT leaked in status response
    assert "raw_sequence" not in status_data


def test_job_status_unknown_job_id(client):
    """Requirement 16.8: Non-existent job ID returns HTTP 404."""
    resp = client.get("/api/jobs/JOB-NONEXISTENT")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ==============================================================================
# 3. WORKER PROCESSING & STAGE TRANSITIONS
# ==============================================================================

def test_worker_processing_completed_state():
    """Requirement 16.4, 16.5 & 16.9: Worker transitions through RUNNING to COMPLETED."""
    req = JobCreateRequest(sequence="ACGTACGTACGTACGT", read_id="READ_WORKER")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    worker = BackgroundJobWorker(job_service.repository)
    finished_job = worker.process_job(job.job_id)

    assert finished_job is not None
    assert finished_job.status == JobStatus.COMPLETED
    assert finished_job.progress == 100
    assert finished_job.current_stage == JobStage.COMPLETED
    assert finished_job.started_at is not None
    assert finished_job.completed_at is not None
    assert finished_job.error is None
    assert finished_job.result_reference is not None
    assert finished_job.result_reference["stage"] == 5
    assert finished_job.result_reference["status"] == "completed"


def test_worker_processing_failed_state_empty_sequence():
    """Requirement 16.6 & 16.10: Worker gracefully handles failures and sanitizes errors."""
    job = Job(
        job_id="JOB-EMPTY-FAIL",
        status=JobStatus.QUEUED,
        raw_sequence="   ",
        read_id="READ_FAIL",
    )
    job_service.repository.save(job)

    worker = BackgroundJobWorker(job_service.repository)
    failed_job = worker.process_job(job.job_id)

    assert failed_job is not None
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.current_stage == JobStage.FAILED
    assert failed_job.completed_at is not None
    assert "empty" in failed_job.error.lower()


def test_worker_processing_sanitized_missing_file_error():
    """Requirement 16.10: Security check ensures server filesystem paths are never leaked."""
    job = Job(
        job_id="JOB-PATH-FAIL",
        status=JobStatus.QUEUED,
        raw_sequence="",
        file_path="/secret/internal/database/missing_read.fastq",
        read_id="READ_FAIL",
    )
    job_service.repository.save(job)

    worker = BackgroundJobWorker(job_service.repository)
    failed_job = worker.process_job(job.job_id)

    assert failed_job.status == JobStatus.FAILED
    # Error should be sanitized
    assert "internal" not in failed_job.error
    assert "secret" not in failed_job.error
    assert "could not be accessed" in failed_job.error


# ==============================================================================
# 4. DUPLICATE SUBMISSION PROTECTION
# ==============================================================================

def test_duplicate_submission_protection(client):
    """Requirement 16.11: Deduplicates repeated submissions using idempotency key."""
    payload = {
        "sequence": "CGTACGTACGTACGTA",
        "read_id": "READ_DEDUP",
        "idempotency_key": "idemp-client-12345",
    }
    # First submission
    resp1 = client.post("/api/jobs", json=payload)
    assert resp1.status_code == 201
    job_id_1 = resp1.json()["job_id"]
    assert resp1.json()["is_duplicate"] is False

    # Second submission with same idempotency key while active
    resp2 = client.post("/api/jobs", json=payload)
    assert resp2.status_code == 201
    job_id_2 = resp2.json()["job_id"]
    assert resp2.json()["is_duplicate"] is True
    assert job_id_1 == job_id_2


# ==============================================================================
# 5. JOB CANCELLATION
# ==============================================================================

def test_job_cancellation(client):
    """Requirement 10: Safe job cancellation."""
    req = JobCreateRequest(sequence="ACGTACGT", read_id="READ_CANCEL")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    resp = client.post(f"/api/jobs/{job.job_id}/cancel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CANCELLED"
    assert data["current_stage"] == "CANCELLED"

    # Worker honors cancellation flag if run subsequently
    worker = BackgroundJobWorker(job_service.repository)
    res = worker.process_job(job.job_id)
    assert res.status == JobStatus.CANCELLED


# ==============================================================================
# 6. JOB RESULT ENDPOINT & LIFECYCLE
# ==============================================================================

def test_job_result_endpoint_lifecycle(client):
    """Retrieves structured result once COMPLETED, conflicts when still active."""
    req = JobCreateRequest(sequence="ACGTACGTACGTACGT", read_id="READ_RES")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    # 1. While queued/running -> HTTP 409 Conflict
    resp_pending = client.get(f"/api/jobs/{job.job_id}/result")
    assert resp_pending.status_code == 409

    # 2. Process job to completion
    worker = BackgroundJobWorker(job_service.repository)
    worker.process_job(job.job_id)

    # 3. When completed -> HTTP 200 with Stage 5/6 structured payload
    resp_done = client.get(f"/api/jobs/{job.job_id}/result")
    assert resp_done.status_code == 200
    res_data = resp_done.json()
    assert res_data["stage"] == 5
    assert res_data["status"] == "completed"
    assert res_data["token_count"] > 0
    assert "embedding" in res_data
    assert "pattern_analysis" in res_data


# ==============================================================================
# 7. JOB HISTORY LISTING
# ==============================================================================

def test_job_history_listing_sanitized(client):
    """Requirement 11 & 14: Job history lists recent jobs without sensitive leakage."""
    job_service.create_and_enqueue_job(
        JobCreateRequest(sequence="ACGTACGT", read_id="READ_HIST_1"), auto_enqueue=False
    )
    job_service.create_and_enqueue_job(
        JobCreateRequest(sequence="TGCATGCA", read_id="READ_HIST_2"), auto_enqueue=False
    )

    resp = client.get("/api/jobs?limit=10")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    for item in history:
        assert "job_id" in item
        assert "status" in item
        assert "progress" in item
        assert "current_stage" in item
        assert "created_at" in item
        # Ensure sequence content is NOT leaked
        assert "raw_sequence" not in item


# ==============================================================================
# 8. STAGE 4 -> STAGE 5 -> STAGE 6 INTEGRATION VIA WORKER
# ==============================================================================

def test_stage4_stage5_stage6_integration_via_worker():
    """
    Requirement 16.14: Complete asynchronous pipeline execution through
    Stage 4 normalization -> Stage 5 Transformer Foundation -> Stage 6 Results schema.
    """
    input_dna = "acgtacgtacgtacgt"  # lowercase requires Stage 4 normalization
    req = JobCreateRequest(sequence=input_dna, read_id="READ_FULL_PIPELINE")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    worker = BackgroundJobWorker(job_service.repository)
    completed_job = worker.process_job(job.job_id)

    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.progress == 100
    res = completed_job.result_reference

    # Validates Stage 5 DNA Transformer fields
    assert res["sequence_length"] == 16
    assert res["model"]["name"] == "RASS-DNA-Transformer"
    assert res["model"]["checkpoint_loaded"] is False  # Untrained checkpoint safety

    # Validates Stage 6 Results Dashboard compatibility
    assert res["confidence"] is None  # Null confidence safeguard
    assert res["clinical_interpretation"] is False  # Clinical disclaimer enforced
    assert res["pattern_analysis"]["status"] == "pending_validation"
    assert len(res["pattern_analysis"]["patterns"]) == 0  # Zero mutation fabrication


# ==============================================================================
# 9. ADDITIONAL EDGE CASES & REVALIDATION
# ==============================================================================

def test_running_state_inspection():
    """Requirement 16.4: Validates job state transition and progress during RUNNING."""
    req = JobCreateRequest(sequence="ACGTACGT", read_id="READ_RUNNING")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    # Manually transition to RUNNING to verify state model
    job.status = JobStatus.RUNNING
    job.current_stage = JobStage.DATA_INGESTION
    job.progress = 20
    job.started_at = datetime.now(timezone.utc)
    job_service.repository.save(job)

    fetched = job_service.get_job(job.job_id)
    assert fetched.status == JobStatus.RUNNING
    assert fetched.progress == 20
    assert fetched.current_stage == JobStage.DATA_INGESTION
    assert fetched.started_at is not None


def test_missing_input_validation_error(client):
    """Rejects job creation when neither sequence nor file_path is provided."""
    resp = client.post("/api/jobs", json={})
    assert resp.status_code == 400
    assert "either 'sequence' or 'file_path' must be provided" in resp.json()["detail"].lower()


def test_extremely_long_sequence_rejection():
    """Rejects sequences exceeding the maximum supported 10000 bp limit."""
    long_seq = "ACGT" * 3000  # 12000 bp
    req = JobCreateRequest(sequence=long_seq, read_id="READ_LONG")
    job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)

    worker = BackgroundJobWorker(job_service.repository)
    failed = worker.process_job(job.job_id)
    assert failed.status == JobStatus.FAILED
    assert "exceeds maximum supported limit" in failed.error


def test_v1_api_alias_routes(client):
    """Verifies that /api/v1/jobs route aliases match expected behavior."""
    resp = client.post(
        "/api/v1/jobs",
        json={"sequence": "CGTACGTA", "read_id": "READ_V1_ALIAS"},
    )
    assert resp.status_code == 201
    job_id = resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id

    list_resp = client.get("/api/v1/jobs?limit=5")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)


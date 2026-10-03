"""
RASS-BUILDER: Stage 10 Production Hardening, Security & Observability Test Suite
Tests:
- Security HTTP response headers
- Request correlation ID propagation
- Explicit CORS and size limits
- Input validation and path traversal defense
- Oversized and malformed FASTQ/FASTA rejection
- Rate limiting and HTTP 429 response
- Audit logging of security-relevant events
- Consistent API error responses
- Operational health and readiness endpoints
- Async worker terminal failure guarantees
- Database safety and transactional integrity
- Prevention of secret and internal path leakage
"""

import io
import pytest
from starlette.testclient import TestClient

from main import app
from core.rate_limiter import rate_limiter
from core.correlation import get_current_request_id
from core.logger import redact_sensitive_data
from core.audit import get_recent_audit_logs, record_audit_event, AuditEventType
from core.metrics import metrics_collector
from database.connection import get_db_connection
from database.schema import init_db
from jobs.service import job_service
from jobs.models import JobCreateRequest, JobStatus
from auth.repository import user_repository
from auth.models import UserRole


@pytest.fixture
def client():
    """Provides test client with fresh database initialization."""
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_state():
    """Resets rate limiter, metrics, users, and jobs between test executions."""
    rate_limiter.reset()
    user_repository.clear()
    job_service.clear()
    yield
    rate_limiter.reset()
    user_repository.clear()
    job_service.clear()


# ==============================================================================
# 1. SECURITY HEADERS & CORS
# ==============================================================================

def test_security_headers_present_on_all_responses(client):
    """Verifies production security headers are attached to API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert "default-src" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in headers
    assert headers["X-Request-ID"].startswith("req_")


def test_cors_explicit_configuration(client):
    """Verifies CORS headers honor allowed origin rules."""
    origin = "http://localhost:5173"
    resp = client.options(
        "/api/jobs",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == origin


# ==============================================================================
# 2. REQUEST CORRELATION
# ==============================================================================

def test_request_id_generation_and_propagation(client):
    """Verifies client-provided X-Request-ID is preserved and reflected in response."""
    custom_id = "test-corr-trace-9999"
    resp = client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id


# ==============================================================================
# 3. HEALTH & READINESS ENDPOINTS
# ==============================================================================

def test_health_endpoint(client):
    """Verifies lightweight /health and /api/v1/health operational process status."""
    for path in ("/health", "/api/v1/health"):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "rass-builder-api"
        assert "timestamp" in data
        # Ensure no sensitive credentials or internal paths are returned
        assert "password" not in str(data).lower()
        assert "secret" not in str(data).lower()


def test_readiness_endpoint_verifies_dependencies(client):
    """Verifies deep dependency check /ready evaluates database, worker, and storage."""
    for path in ("/ready", "/api/v1/ready"):
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["database"] == "ok"
        assert data["dependencies"]["storage"] == "ok"


# ==============================================================================
# 4. RATE LIMITING & ABUSE PROTECTION
# ==============================================================================

def test_rate_limiting_enforcement(client):
    """Verifies HTTP 429 is returned with Retry-After when requests exceed threshold."""
    # Enforce limit using rate_limiter directly or via rapid requests with custom IP
    test_ip = "198.51.100.42"
    # Rapidly send requests to auth endpoint with forwarded IP
    blocked = False
    for i in range(110):
        resp = client.post(
            "/api/auth/login",
            json={"email": f"bot_{i}@test.com", "password": "WrongPassword123!"},
            headers={"X-Forwarded-For": test_ip},
        )
        if resp.status_code == 429:
            blocked = True
            assert "Retry-After" in resp.headers
            err_data = resp.json()
            assert err_data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert "Rate limit exceeded" in err_data["detail"]
            break

    assert blocked, "Expected client to be rate-limited with HTTP 429 after rapid requests."


# ==============================================================================
# 5. AUDIT LOGGING
# ==============================================================================

def test_audit_event_creation_and_redaction(client):
    """Verifies security-relevant events are audited and credentials/sequences are redacted."""
    # 1. Login failure audit
    client.post(
        "/api/auth/login",
        json={"email": "nonexistent_audit@biolab.org", "password": "SecretPassword123!"},
    )

    logs = get_recent_audit_logs(limit=10, event_type=AuditEventType.LOGIN_FAILURE)
    assert len(logs) > 0
    latest = logs[0]
    assert latest["event_type"] == AuditEventType.LOGIN_FAILURE
    assert latest["status"] == "FAILURE"
    # Ensure password was NOT logged
    assert "SecretPassword123!" not in str(latest["details"])
    assert latest["request_id"].startswith("req_")


def test_audit_event_for_file_upload(client):
    """Verifies file upload triggers an audit event."""
    valid_fastq = (
        "@READ_AUDIT\n"
        "ACTGACTGACTG\n"
        "+\n"
        "IIIIIIIIIIII\n"
    ).encode("utf-8")

    client.post(
        "/api/v1/uploads/fastq",
        files={"file": ("audit_sample.fastq", valid_fastq, "text/plain")},
    )

    logs = get_recent_audit_logs(limit=10, event_type=AuditEventType.FILE_UPLOAD)
    assert len(logs) > 0
    assert logs[0]["details"]["filename"] == "audit_sample.fastq"
    assert logs[0]["details"]["format"] == "FASTQ"


# ==============================================================================
# 6. INPUT VALIDATION & FILE SECURITY
# ==============================================================================

def test_upload_empty_file_rejected(client):
    """Verifies 0-byte file uploads are rejected safely."""
    resp = client.post(
        "/api/v1/uploads/fastq",
        files={"file": ("empty.fastq", b"", "text/plain")},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_upload_unsupported_file_extension(client):
    """Verifies non-FASTQ/FASTA formats are rejected safely."""
    resp = client.post(
        "/api/v1/uploads/fastq",
        files={"file": ("malicious.exe", b"binary_data", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "unsupported" in resp.json()["detail"].lower()


def test_upload_path_traversal_prevention(client):
    """Verifies path traversal filenames are sanitized and cannot escape uploads/."""
    valid_fastq = (
        "@READ_TRAVERSAL\n"
        "ACGTACGT\n"
        "+\n"
        "IIIIIIII\n"
    ).encode("utf-8")

    # Attempt path traversal in filename
    resp = client.post(
        "/api/v1/uploads/fastq",
        files={"file": ("../../escape.fastq", valid_fastq, "text/plain")},
    )
    assert resp.status_code == 200
    # Base filename must be sanitized to escape.fastq without ../ components
    assert resp.json()["filename"] == "escape.fastq"


def test_malformed_fastq_rejection(client):
    """Verifies malformed FASTQ records (missing @ header) are rejected with HTTP 400."""
    malformed = (
        ">FASTA_HEADER_NOT_FASTQ\n"
        "ACGTACGT\n"
        "+\n"
        "IIIIIIII\n"
    ).encode("utf-8")

    resp = client.post(
        "/api/v1/uploads/fastq",
        files={"file": ("corrupt.fastq", malformed, "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "BAD_REQUEST"


def test_fasta_upload_and_validation(client):
    """Verifies FASTA endpoint validates headers and parses sequence records."""
    valid_fasta = (
        ">GENE_TP53 Tumor suppressor gene\n"
        "ACTGACTGACTGACTG\n"
        ">GENE_BRCA1 DNA repair gene\n"
        "CGTACGTACGTACGTA\n"
    ).encode("utf-8")

    resp = client.post(
        "/api/v1/uploads/fasta",
        files={"file": ("reference.fasta", valid_fasta, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "FASTA"
    assert data["record_count"] == 2
    assert data["first_record_id"] == "GENE_TP53"


# ==============================================================================
# 7. CONSISTENT ERROR RESPONSES & DATA LEAKAGE PREVENTION
# ==============================================================================

def test_consistent_error_response_structure_on_404(client):
    """Verifies standard { error: { code, message, request_id }, detail } response on 404."""
    resp = client.get("/api/nonexistent-endpoint-12345")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]
    assert "detail" in data


def test_unauthenticated_protected_endpoint_returns_401(client):
    """Verifies unauthenticated access to admin endpoint returns 401 with standard error."""
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401
    data = resp.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "detail" in data


def test_insufficient_authorization_returns_403(client):
    """Verifies standard user role cannot access admin endpoint (403 Forbidden)."""
    # Register standard user
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Standard Auditor",
            "email": "auditor_stage10@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "USER",
        },
    ).json()
    token = reg["access_token"]

    resp = client.get(
        "/api/admin/system/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "FORBIDDEN"


def test_secrets_and_stack_traces_never_leaked_in_errors(client):
    """Verifies responses never leak stack traces, database credentials, or secret keys."""
    # Trigger 422 validation error
    resp = client.post("/api/jobs", json={"sequence": 12345})  # Invalid type
    assert resp.status_code == 422
    body = resp.text
    assert "traceback" not in body.lower()
    assert "password" not in body.lower()
    assert "secret" not in body.lower()
    assert "c:\\" not in body.lower()
    assert "/users/" not in body.lower()


def test_sensitive_data_redaction_function():
    """Verifies the redaction filter masks passwords, bearer tokens, and long sequences."""
    raw = (
        'User login payload: password="SuperSecretPassword123!" with '
        'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz and '
        'sequence: ACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTGACTG'
    )
    redacted = redact_sensitive_data(raw)
    assert "SuperSecretPassword123!" not in redacted
    assert "[REDACTED]" in redacted
    assert "[REDACTED_TOKEN]" in redacted
    assert "DNA_SEQUENCE_" in redacted


# ==============================================================================
# 8. ASYNC WORKER RELIABILITY & FAILURE HANDLING
# ==============================================================================

def test_worker_failure_guarantees_terminal_state(client):
    """Verifies unhandled worker errors always transition job to terminal FAILED status."""
    # Enqueue a job with a sequence that will fail normalization / analysis
    req = JobCreateRequest(sequence="   ")  # Whitespace only
    try:
        job, _ = job_service.create_and_enqueue_job(req, auto_enqueue=False)
    except ValueError:
        # Create directly via job model to test worker error handling on invalid job payload
        from jobs.models import Job, JobStage
        job = Job(
            job_id="JOB-FAIL-TEST",
            raw_sequence="",
            status=JobStatus.QUEUED,
            current_stage=JobStage.QUEUED,
        )
        job_service.repository.save(job)

    # Execute worker processing synchronously to observe error handling
    finished_job = job_service.worker.process_job(job.job_id)
    assert finished_job is not None
    assert finished_job.status == JobStatus.FAILED
    assert finished_job.current_stage == JobStage.FAILED
    assert finished_job.completed_at is not None
    assert finished_job.error is not None
    # Verify job error is sanitized and does not contain internal tracebacks
    assert "traceback" not in finished_job.error.lower()


# ==============================================================================
# 9. OBSERVABILITY & ADMIN METRICS
# ==============================================================================

def test_admin_metrics_and_audit_endpoints(client):
    """Verifies admin role can query metrics summary and audit logs."""
    # Register an admin user
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Super Admin",
            "email": "super_admin_stage10@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "ADMIN",
        },
    ).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query metrics
    resp_metrics = client.get("/api/admin/metrics", headers=headers)
    assert resp_metrics.status_code == 200
    metrics_data = resp_metrics.json()["metrics"]
    assert "http_metrics" in metrics_data
    assert "job_pipeline_metrics" in metrics_data
    assert "system_errors" in metrics_data

    # Query audit logs
    resp_audit = client.get("/api/admin/audit-logs", headers=headers)
    assert resp_audit.status_code == 200
    audit_data = resp_audit.json()
    assert audit_data["status"] == "success"
    assert isinstance(audit_data["audit_logs"], list)

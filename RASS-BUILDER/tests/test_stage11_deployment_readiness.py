"""
RASS-BUILDER: Stage 11 Deployment, CI/CD & Production Readiness Test Suite
Tests:
- Environment configuration and .env.example completeness
- Dependency specifications in requirements.txt & requirements-dev.txt
- Dockerfile & docker-compose configuration and healthcheck definition
- GitHub Actions CI workflow structure and syntax
- Deterministic database initialization script
- Standalone background worker process capability
- Configurable PyTorch model checkpoint paths
- Frontend SPA production build and static asset delivery
- Repository hygiene and .gitignore rules
- Graceful shutdown mechanics
"""

import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
import yaml
from starlette.testclient import TestClient

from main import app
from database.schema import init_db, CURRENT_SCHEMA_VERSION
from database.repository import SqliteJobRepository
from models.stage5_engine import Stage5DNAEngine
from jobs.service import job_service


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# 1. ENVIRONMENT CONFIGURATION & .ENV TEMPLATE
# ==============================================================================

def test_env_example_contains_all_production_variables():
    """Requirement 3: Verifies .env.example documents all essential variables."""
    env_example = PROJECT_ROOT / ".env.example"
    assert env_example.exists(), ".env.example must exist in project root."
    content = env_example.read_text(encoding="utf-8")

    expected_vars = [
        "RASS_ENV",
        "RASS_LOG_LEVEL",
        "RASS_DB_PATH",
        "RASS_CORS_ORIGINS",
        "RASS_MAX_UPLOAD_SIZE_MB",
        "RASS_RATE_LIMIT_ENABLED",
        "RASS_REQUIRE_AUTH",
    ]
    for var in expected_vars:
        assert var in content, f"Variable {var} missing from .env.example."


# ==============================================================================
# 2. DEPENDENCY MANAGEMENT
# ==============================================================================

def test_requirements_files_completeness():
    """Requirement 2: Verifies requirements.txt specifies all runtime dependencies."""
    req_file = PROJECT_ROOT / "requirements.txt"
    dev_req_file = PROJECT_ROOT / "requirements-dev.txt"

    assert req_file.exists(), "requirements.txt must exist in project root."
    assert dev_req_file.exists(), "requirements-dev.txt must exist in project root."

    content = req_file.read_text(encoding="utf-8")
    assert "fastapi" in content
    assert "uvicorn" in content
    assert "torch" in content
    assert "pydantic" in content
    assert "starlette" in content

    dev_content = dev_req_file.read_text(encoding="utf-8")
    assert "pytest" in dev_content


# ==============================================================================
# 3. DOCKER & CONTAINER READINESS
# ==============================================================================

def test_dockerfile_configuration_and_healthcheck():
    """Requirements 4 & 5: Verifies Dockerfile has unprivileged user and healthcheck."""
    dockerfile = PROJECT_ROOT / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile must exist in project root."
    content = dockerfile.read_text(encoding="utf-8")

    assert "FROM python:" in content
    assert "appuser" in content, "Dockerfile should use an unprivileged user."
    assert "USER appuser" in content
    assert "HEALTHCHECK" in content, "Dockerfile must define container healthcheck."
    assert "/health" in content, "Healthcheck should query /health probe."
    assert "EXPOSE 8000" in content


def test_docker_compose_configuration():
    """Requirement 4: Verifies docker-compose.yml defines services and volumes."""
    compose_file = PROJECT_ROOT / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml must exist in project root."
    content = compose_file.read_text(encoding="utf-8")

    parsed = yaml.safe_load(content)
    assert "services" in parsed
    assert "rass-web" in parsed["services"]
    assert "volumes" in parsed
    assert "healthcheck" in parsed["services"]["rass-web"]


# ==============================================================================
# 4. CI PIPELINE WORKFLOW
# ==============================================================================

def test_ci_pipeline_workflow_validity():
    """Requirement 6: Verifies .github/workflows/ci.yml structure and matrix."""
    ci_file = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.exists(), "CI workflow .github/workflows/ci.yml must exist."
    content = ci_file.read_text(encoding="utf-8")

    parsed = yaml.safe_load(content)
    assert "jobs" in parsed
    assert "backend-test-matrix" in parsed["jobs"]
    assert "frontend-build" in parsed["jobs"]


# ==============================================================================
# 5. DETERMINISTIC DATABASE INITIALIZATION
# ==============================================================================

def test_deterministic_database_initialization_on_clean_path():
    """Requirement 8: Verifies database schema can initialize deterministically."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db = Path(tmp_dir) / "fresh_test.db"
        assert not test_db.exists()

        init_db(test_db)
        assert test_db.exists()

        conn = sqlite3.connect(str(test_db))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        required_tables = [
            "jobs",
            "analysis_results",
            "users",
            "sessions",
            "audit_logs",
            "schema_versions",
        ]
        for tbl in required_tables:
            assert tbl in tables, f"Required table '{tbl}' was not created during init."


# ==============================================================================
# 6. CONFIGURABLE PYTORCH MODEL PATHS
# ==============================================================================

def test_configurable_model_path_handling():
    """Requirement 9: Verifies custom RASS_MODEL_PATH is honored with clear missing status."""
    nonexistent = Path("nonexistent_model_checkpoint.pt")
    os.environ["RASS_MODEL_PATH"] = str(nonexistent)

    try:
        engine = Stage5DNAEngine()
        assert not engine.checkpoint_loaded
        assert "Configured model checkpoint not found" in engine.checkpoint_status
    finally:
        os.environ.pop("RASS_MODEL_PATH", None)


# ==============================================================================
# 7. STANDALONE WORKER PROCESS READINESS
# ==============================================================================

def test_standalone_worker_script_and_repository_support():
    """Requirement 14: Verifies standalone worker script exists and can query queue."""
    worker_script = PROJECT_ROOT / "backend" / "scripts" / "run_worker.py"
    assert worker_script.exists(), "Standalone worker script backend/scripts/run_worker.py must exist."

    # Test repository support for worker
    repo = SqliteJobRepository()
    queued = repo.get_queued_jobs(limit=10)
    assert isinstance(queued, list)


# ==============================================================================
# 8. FRONTEND STATIC FILE INTEGRATION
# ==============================================================================

def test_frontend_spa_serving_and_content_negotiation(client):
    """Requirement 10: Verifies browser text/html requests receive SPA index.html."""
    dist_index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        # Browser request with text/html
        resp_html = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
        assert resp_html.status_code == 200
        assert "<html" in resp_html.text.lower() or "<!doctype" in resp_html.text.lower()

        # Direct /app endpoint
        resp_app = client.get("/app")
        assert resp_app.status_code == 200
        assert "<html" in resp_app.text.lower() or "<!doctype" in resp_app.text.lower()

    # API JSON client request
    resp_json = client.get("/", headers={"Accept": "application/json"})
    assert resp_json.status_code == 200
    assert resp_json.json()["name"] == "RASS-BUILDER"


# ==============================================================================
# 9. REPOSITORY HYGIENE & GITIGNORE
# ==============================================================================

def test_gitignore_covers_sensitive_and_large_files():
    """Requirement 15: Verifies .gitignore excludes envs, databases, checkpoints, caches."""
    gitignore = PROJECT_ROOT / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")

    assert ".env" in content
    assert "*.db" in content
    assert "*.pt" in content or "*.pth" in content
    assert ".pytest_cache" in content
    assert "node_modules" in content


# ==============================================================================
# 10. GRACEFUL SHUTDOWN
# ==============================================================================

def test_graceful_shutdown_mechanism():
    """Requirement 13: Verifies worker stop method sets termination event cleanly."""
    if job_service.worker:
        job_service.worker.start()
        assert job_service.worker.is_running
        job_service.worker.stop()
        assert job_service.worker._stop_event.is_set()

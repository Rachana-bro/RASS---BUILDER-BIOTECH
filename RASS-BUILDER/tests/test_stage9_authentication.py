"""
RASS-BUILDER: Stage 9 Authentication & Role-Based Access Control Tests
Validates:
1. User registration & input validation
2. PBKDF2 HMAC SHA-256 password hashing & constant-time verification
3. Successful user login & bearer token generation
4. Failed login handling (incorrect credentials, non-existent users)
5. Logout & session token revocation
6. Session expiration handling
7. Unauthorized API request blocking (HTTP 401)
8. Authorized API request processing (HTTP 200/201)
9. USER role permissions & access boundaries
10. ADMIN role permissions & administrative endpoints
11. Cross-user result access prevention (IDOR prevention on /api/jobs/{id}/result)
12. Cross-user job status and cancellation prevention (IDOR prevention on /api/jobs/{id})
13. User data isolation in job history listings
14. Stage 8 database compatibility with user-associated jobs
15. Account status enforcement (suspended account handling)
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from main import app
from auth.models import User, UserRole, AccountStatus
from auth.security import hash_password, verify_password, validate_password_strength
from auth.repository import user_repository
from jobs.models import JobCreateRequest, JobStatus
from jobs.service import job_service


@pytest.fixture(autouse=True)
def clean_state():
    """Isolate users, sessions, and jobs between tests."""
    job_service.clear()
    user_repository.clear()
    yield
    job_service.clear()
    user_repository.clear()


@pytest.fixture
def client():
    return TestClient(app)



# ==============================================================================
# 1. PASSWORD HASHING & SECURITY PRIMITIVES
# ==============================================================================

def test_password_hashing_pbkdf2():
    """Requirement 1: Secure PBKDF2 hashing with unique salts; never plaintext."""
    pwd = "Secur3Password!2026"
    hash1, salt1 = hash_password(pwd)
    hash2, salt2 = hash_password(pwd)

    # Different salts must yield different hashes
    assert salt1 != salt2
    assert hash1 != hash2
    assert hash1 != pwd
    assert len(hash1) == 64  # SHA-256 hex digest length
    assert len(salt1) == 32  # 16 bytes hex

    # Verification must succeed for correct password and fail for wrong password
    assert verify_password(pwd, salt1, hash1) is True
    assert verify_password("WrongPassword123!", salt1, hash1) is False
    assert verify_password(pwd, salt2, hash1) is False


def test_password_strength_validation():
    """Requirement 1: Password complexity enforcement."""
    # Too short (< 8)
    valid, msg = validate_password_strength("Short1!")
    assert valid is False
    assert "8 characters" in msg

    # No numbers/special characters
    valid, msg = validate_password_strength("OnlyLettersHere")
    assert valid is False
    assert "number or special character" in msg

    # Valid password
    valid, msg = validate_password_strength("ValidPassword123!")
    assert valid is True
    assert msg == ""


# ==============================================================================
# 2. USER REGISTRATION
# ==============================================================================

def test_user_registration_success(client):
    """Requirement 1 & 2: User registration creates active account and returns token."""
    payload = {
        "name": "Dr. Rosalind Franklin",
        "email": "rosalind@genomics.lab",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "USER",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Dr. Rosalind Franklin"
    assert data["user"]["email"] == "rosalind@genomics.lab"
    assert data["user"]["role"] == "USER"
    assert data["user"]["account_status"] == "ACTIVE"

    # Verify user exists in database and password is NOT plaintext
    db_user = user_repository.get_user_by_email("rosalind@genomics.lab")
    assert db_user is not None
    assert db_user.password_hash != "Password123!"
    assert verify_password("Password123!", db_user.salt, db_user.password_hash) is True


def test_user_registration_duplicate_email(client):
    """Requirement 1: Duplicate registrations are rejected with HTTP 400."""
    payload = {
        "name": "User One",
        "email": "duplicate@lab.org",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


def test_user_registration_password_mismatch(client):
    """Requirement 1: Mismatched password confirmation rejected."""
    payload = {
        "name": "Mismatch User",
        "email": "mismatch@lab.org",
        "password": "Password123!",
        "confirm_password": "DifferentPassword123!",
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "do not match" in resp.json()["detail"].lower()


def test_user_registration_weak_password(client):
    """Requirement 1: Weak password rejected (both length and complexity)."""
    # 1. Under minimum length (triggers validation error 422)
    resp_short = client.post(
        "/api/auth/register",
        json={
            "name": "Weak User",
            "email": "weak@lab.org",
            "password": "weak",
            "confirm_password": "weak",
        },
    )
    assert resp_short.status_code in (400, 422)

    # 2. Length >= 8 but lacking number or special character (triggers complexity 400)
    resp_no_digits = client.post(
        "/api/auth/register",
        json={
            "name": "No Digit User",
            "email": "nodigit@lab.org",
            "password": "weakpasswordonlyletters",
            "confirm_password": "weakpasswordonlyletters",
        },
    )
    assert resp_no_digits.status_code == 400
    assert "number or special character" in resp_no_digits.json()["detail"].lower()



# ==============================================================================
# 3. USER LOGIN & SESSIONS
# ==============================================================================

def test_user_login_success(client):
    """Requirement 1 & 5: Valid login returns bearer token."""
    # Register first
    client.post(
        "/api/auth/register",
        json={
            "name": "James Watson",
            "email": "watson@dna.org",
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        },
    )

    # Login
    resp = client.post(
        "/api/auth/login",
        json={"email": "watson@dna.org", "password": "ValidPassword123!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "watson@dna.org"


def test_user_login_invalid_password(client):
    """Requirement 1: Incorrect password returns HTTP 401."""
    client.post(
        "/api/auth/register",
        json={
            "name": "Francis Crick",
            "email": "crick@dna.org",
            "password": "ValidPassword123!",
            "confirm_password": "ValidPassword123!",
        },
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": "crick@dna.org", "password": "WrongPassword999!"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


def test_user_login_nonexistent_user(client):
    """Requirement 1: Non-existent email returns HTTP 401 without exposing account existence."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "ghost@dna.org", "password": "AnyPassword123!"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


def test_user_logout_revokes_token(client):
    """Requirement 1 & 5: Logout invalidates active session token."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Logout Tester",
            "email": "logout@test.lab",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()
    token = reg["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Verify token works on /api/auth/me
    me_resp = client.get("/api/auth/me", headers=auth_header)
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/auth/logout", headers=auth_header)
    assert logout_resp.status_code == 200

    # Re-accessing /api/auth/me must return 401
    revoked_resp = client.get("/api/auth/me", headers=auth_header)
    assert revoked_resp.status_code == 401


def test_session_expiration(client):
    """Requirement 5: Expired tokens are rejected with HTTP 401."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Expire Test",
            "email": "expire@test.lab",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()
    token = reg["access_token"]
    user_id = reg["user"]["user_id"]

    # Manually expire the session in repository
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    from database.connection import get_db_connection
    with get_db_connection(user_repository.db_path) as conn:
        conn.execute(
            "UPDATE sessions SET expires_at = ? WHERE token = ?;",
            (past_time.isoformat(), token),
        )

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()



# ==============================================================================
# 4. ROLE-BASED ACCESS CONTROL (USER vs ADMIN)
# ==============================================================================

def test_user_role_cannot_access_admin_endpoints(client):
    """Requirement 3: Standard USER role receives HTTP 403 on admin routes."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Standard User",
            "email": "stduser@lab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "USER",
        },
    ).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Accessing admin users list
    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 403
    assert "administrative privileges" in resp.json()["detail"].lower()

    # Accessing admin system status
    resp_sys = client.get("/api/admin/system/status", headers=headers)
    assert resp_sys.status_code == 403


def test_admin_role_can_access_admin_endpoints(client):
    """Requirement 3: ADMIN role can access administrative monitoring and user lists."""
    admin_reg = client.post(
        "/api/auth/register",
        json={
            "name": "Laboratory Admin",
            "email": "admin@lab.org",
            "password": "AdminPassword123!",
            "confirm_password": "AdminPassword123!",
            "role": "ADMIN",
        },
    ).json()
    admin_token = admin_reg["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin user listing
    resp = client.get("/api/admin/users", headers=headers)
    assert resp.status_code == 200
    user_list = resp.json()
    assert len(user_list) >= 1
    assert user_list[0]["email"] == "admin@lab.org"

    # Admin system status
    resp_sys = client.get("/api/admin/system/status", headers=headers)
    assert resp_sys.status_code == 200
    sys_data = resp_sys.json()
    assert sys_data["status"] == "healthy"
    assert "database" in sys_data


def test_unauthenticated_request_to_protected_endpoints(client):
    """Requirement 8: Unauthenticated requests to protected endpoints return HTTP 401."""
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/logout").status_code == 401
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/system/status").status_code == 401


# ==============================================================================
# 5. DATA ISOLATION & IDOR PREVENTION
# ==============================================================================

def test_data_isolation_cross_user_job_status_blocked(client):
    """Requirement 4: User B cannot inspect User A's private analysis job (IDOR)."""
    # 1. Register User A
    user_a = client.post(
        "/api/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()
    token_a = user_a["access_token"]

    # 2. Register User B
    user_b = client.post(
        "/api/auth/register",
        json={
            "name": "User Beta",
            "email": "beta@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()
    token_b = user_b["access_token"]

    # 3. User A creates a job
    create_resp = client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"sequence": "ACGTACGTACGT", "read_id": "READ_ALPHA_1"},
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["job_id"]

    # 4. User A can view their own job
    view_a = client.get(
        f"/api/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert view_a.status_code == 200
    assert view_a.json()["job_id"] == job_id

    # 5. User B tries to view User A's job -> MUST BE 403 FORBIDDEN
    view_b = client.get(
        f"/api/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert view_b.status_code == 403
    assert "permission" in view_b.json()["detail"].lower()


def test_data_isolation_cross_user_result_retrieval_blocked(client):
    """Requirement 4: User B cannot retrieve User A's analysis result (IDOR)."""
    # 1. Register User A and User B
    token_a = client.post(
        "/api/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha2@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    token_b = client.post(
        "/api/auth/register",
        json={
            "name": "User Beta",
            "email": "beta2@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    # 2. User A creates and completes job
    create_resp = client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"sequence": "ACGTACGTACGTACGT", "read_id": "READ_ALPHA_RES"},
    )
    job_id = create_resp.json()["job_id"]

    # Ensure the job is completed by background worker or process it directly
    import time
    for _ in range(60):
        jb = job_service.get_job(job_id)
        if jb and jb.status == JobStatus.COMPLETED:
            break
        time.sleep(0.05)
    else:
        from jobs.worker import BackgroundJobWorker
        worker = BackgroundJobWorker(job_service.repository)
        worker.process_job(job_id)

    # 3. User A can fetch results
    res_a = client.get(
        f"/api/jobs/{job_id}/result",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200

    # 4. User B tries to fetch User A's result -> MUST BE 403 FORBIDDEN
    res_b = client.get(
        f"/api/jobs/{job_id}/result",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 403


def test_data_isolation_cross_user_cancellation_blocked(client):
    """Requirement 4: User B cannot cancel User A's job."""
    token_a = client.post(
        "/api/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha3@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    token_b = client.post(
        "/api/auth/register",
        json={
            "name": "User Beta",
            "email": "beta3@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    # User A creates job
    job_id = client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"sequence": "TGCATGCATGCA", "read_id": "READ_CANCEL_ISO"},
    ).json()["job_id"]

    # User B tries to cancel -> 403
    cancel_b = client.post(
        f"/api/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert cancel_b.status_code == 403


def test_data_isolation_job_history_filtered_by_user(client):
    """Requirement 4: User only sees their own jobs in job history table; Admin sees all."""
    token_a = client.post(
        "/api/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha4@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    token_b = client.post(
        "/api/auth/register",
        json={
            "name": "User Beta",
            "email": "beta4@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    token_admin = client.post(
        "/api/auth/register",
        json={
            "name": "Admin User",
            "email": "admin4@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "ADMIN",
        },
    ).json()["access_token"]

    # User A creates 2 jobs
    client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"sequence": "AAAAAAAAGGGG", "read_id": "READ_A1"},
    )
    client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"sequence": "CCCCCCCTTTTT", "read_id": "READ_A2"},
    )

    # User B creates 1 job
    client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"sequence": "TGCATGCATGCA", "read_id": "READ_B1"},
    )

    # User A listing: should only contain User A's jobs
    list_a = client.get("/api/jobs", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert len(list_a) == 2
    for j in list_a:
        assert j["read_id"] in ("READ_A1", "READ_A2")

    # User B listing: should only contain User B's job
    list_b = client.get("/api/jobs", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert len(list_b) == 1
    assert list_b[0]["read_id"] == "READ_B1"

    # Admin listing: should see all 3 jobs
    list_admin = client.get("/api/jobs", headers={"Authorization": f"Bearer {token_admin}"}).json()
    assert len(list_admin) == 3


def test_admin_can_access_any_user_job(client):
    """Requirement 3: Admin role can view and monitor jobs created by any user."""
    token_user = client.post(
        "/api/auth/register",
        json={
            "name": "Research Fellow",
            "email": "fellow@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()["access_token"]

    token_admin = client.post(
        "/api/auth/register",
        json={
            "name": "Lab Director",
            "email": "director@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "ADMIN",
        },
    ).json()["access_token"]

    job_id = client.post(
        "/api/jobs",
        headers={"Authorization": f"Bearer {token_user}"},
        json={"sequence": "ACGTACGTACGT", "read_id": "READ_FELLOW"},
    ).json()["job_id"]

    # Admin accesses Fellow's job -> 200 OK
    resp = client.get(
        f"/api/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
    assert resp.json()["job_id"] == job_id


# ==============================================================================
# 6. SUSPENDED ACCOUNT ENFORCEMENT
# ==============================================================================

def test_suspended_account_access_forbidden(client):
    """Requirement 10: Suspended accounts cannot log in or perform actions."""
    reg = client.post(
        "/api/auth/register",
        json={
            "name": "Suspended Person",
            "email": "suspended@biolab.org",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    ).json()
    token = reg["access_token"]
    user_id = reg["user"]["user_id"]

    # Mark user account SUSPENDED
    user = user_repository.get_user_by_id(user_id)
    user.account_status = AccountStatus.SUSPENDED
    user_repository.save_user(user)

    # API access with existing token must fail with HTTP 403
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "suspended" in resp.json()["detail"].lower()

    # Login must also fail with HTTP 403
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "suspended@biolab.org", "password": "Password123!"},
    )
    assert login_resp.status_code == 403

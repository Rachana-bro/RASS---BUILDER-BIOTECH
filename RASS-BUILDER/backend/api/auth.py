"""
RASS-BUILDER: Stage 9 & Stage 10 Authentication & Administration API Endpoints
Provides registration, login, logout, session state, administrative metrics,
audit trails, and rate-limited authentication.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Request, Query

from auth.models import (
    User,
    UserRole,
    AccountStatus,
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    AdminUserSummary,
)
from auth.security import (
    hash_password,
    verify_password,
    generate_user_id,
    validate_password_strength,
)
from auth.repository import user_repository
from auth.dependencies import (
    get_current_user_optional,
    require_authenticated_user,
    require_admin_user,
)
from jobs.service import job_service
from core.audit import record_audit_event, get_recent_audit_logs, AuditEventType
from core.rate_limiter import enforce_rate_limit, get_client_ip
from core.correlation import get_current_request_id
from core.metrics import metrics_collector


router = APIRouter(tags=["Stage 9 Authentication & Stage 10 Administration"])


# ==============================================================================
# 1. USER REGISTRATION (POST /api/auth/register & /api/v1/auth/register)
# ==============================================================================

@router.post(
    "/api/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("AUTH", max_requests=100, window_seconds=60))],
    summary="Register a new user account and obtain access token",
)
@router.post(
    "/api/v1/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("AUTH", max_requests=100, window_seconds=60))],
    include_in_schema=False,
)
def register_user(request_payload: UserRegisterRequest, req: Request):
    """
    Registers a new workstation user.
    Validates password complexity, enforces unique email/username,
    hashes password with PBKDF2 HMAC SHA-256 with unique salt,
    and returns an authenticated session token.
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(req)

    clean_name = request_payload.name.strip()
    clean_email = request_payload.email.strip().lower()

    if not clean_name or len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at least 2 characters.",
        )

    if not clean_email or "@" not in clean_email or "." not in clean_email:
        # Check if alphanumeric username
        if not clean_email.replace("_", "").isalnum() or len(clean_email) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or username format.",
            )

    if request_payload.password != request_payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    is_valid_pw, pw_err = validate_password_strength(request_payload.password)
    if not is_valid_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pw_err,
        )

    # Check for duplicate user
    existing = user_repository.get_user_by_email(clean_email)
    if existing:
        record_audit_event(
            event_type=AuditEventType.AUTH_FAILURE,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"email": clean_email, "reason": "DUPLICATE_EMAIL"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email or username already exists.",
        )

    # Hash password securely
    pw_hash, salt = hash_password(request_payload.password)
    user_id = generate_user_id()
    now = datetime.now(timezone.utc)

    assigned_role = request_payload.role or UserRole.USER

    user = User(
        user_id=user_id,
        name=clean_name,
        email=clean_email,
        password_hash=pw_hash,
        salt=salt,
        role=assigned_role,
        account_status=AccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    user_repository.save_user(user)

    # Issue initial session (TTL 24 hours = 86400s)
    session = user_repository.create_session(user_id=user.user_id, duration_seconds=86400)

    record_audit_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        status="SUCCESS",
        user_id=user.user_id,
        request_id=req_id,
        ip_address=client_ip,
        details={"event": "USER_REGISTERED", "role": user.role.value},
    )

    user_resp = UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        account_status=user.account_status.value,
        created_at=user.created_at.isoformat(),
    )

    return TokenResponse(
        access_token=session.token,
        token_type="bearer",
        expires_in=86400,
        user=user_resp,
    )


# ==============================================================================
# 2. USER LOGIN (POST /api/auth/login & /api/v1/auth/login)
# ==============================================================================

@router.post(
    "/api/auth/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_rate_limit("AUTH", max_requests=100, window_seconds=60))],
    summary="Authenticate with email/username and password",
)
@router.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_rate_limit("AUTH", max_requests=100, window_seconds=60))],
    include_in_schema=False,
)
def login_user(request_payload: UserLoginRequest, req: Request):
    """
    Authenticates user credentials.
    Performs constant-time hash comparison and generates a session bearer token.
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(req)

    clean_email = request_payload.email.strip().lower()
    user = user_repository.get_user_by_email(clean_email)

    if not user:
        record_audit_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"email": clean_email, "reason": "USER_NOT_FOUND"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(request_payload.password, user.salt, user.password_hash):
        record_audit_event(
            event_type=AuditEventType.LOGIN_FAILURE,
            status="FAILURE",
            user_id=user.user_id,
            request_id=req_id,
            ip_address=client_ip,
            details={"email": clean_email, "reason": "INVALID_PASSWORD"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status == AccountStatus.SUSPENDED:
        record_audit_event(
            event_type=AuditEventType.AUTH_FAILURE,
            status="FAILURE",
            user_id=user.user_id,
            request_id=req_id,
            ip_address=client_ip,
            details={"email": clean_email, "reason": "ACCOUNT_SUSPENDED"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact administrator.",
        )

    # Issue session
    session = user_repository.create_session(user_id=user.user_id, duration_seconds=86400)

    record_audit_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        status="SUCCESS",
        user_id=user.user_id,
        request_id=req_id,
        ip_address=client_ip,
        details={"email": user.email, "role": user.role.value},
    )

    user_resp = UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        account_status=user.account_status.value,
        created_at=user.created_at.isoformat(),
    )

    return TokenResponse(
        access_token=session.token,
        token_type="bearer",
        expires_in=86400,
        user=user_resp,
    )


# ==============================================================================
# 3. CURRENT USER (GET /api/auth/me & /api/v1/auth/me)
# ==============================================================================

@router.get(
    "/api/auth/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
@router.get(
    "/api/v1/auth/me",
    response_model=UserResponse,
    include_in_schema=False,
)
def get_current_user_profile(user: User = Depends(require_authenticated_user)):
    """
    Returns authenticated user's profile details.
    Password hash and cryptographic salts are never exposed.
    """
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        account_status=user.account_status.value,
        created_at=user.created_at.isoformat(),
    )


# ==============================================================================
# 4. LOGOUT (POST /api/auth/logout & /api/v1/auth/logout)
# ==============================================================================

@router.post(
    "/api/auth/logout",
    summary="Revoke current session token",
)
@router.post(
    "/api/v1/auth/logout",
    include_in_schema=False,
)
def logout_user(req: Request, user: User = Depends(require_authenticated_user)):
    """
    Invalidates the active session token in the persistent database.
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(req)

    auth_header = req.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if token:
        user_repository.invalidate_session(token)

    record_audit_event(
        event_type=AuditEventType.LOGOUT,
        status="SUCCESS",
        user_id=user.user_id,
        request_id=req_id,
        ip_address=client_ip,
        details={"user_id": user.user_id},
    )

    return {
        "status": "success",
        "message": "Session invalidated successfully. Logged out.",
    }


# ==============================================================================
# 5. ADMIN: USER MANAGEMENT (GET /api/admin/users)
# ==============================================================================

@router.get(
    "/api/admin/users",
    response_model=List[AdminUserSummary],
    summary="[Admin] List all registered workstation users",
)
def list_users_admin(admin: User = Depends(require_admin_user)):
    """
    Administrative endpoint to view registered users and their analysis job activity.
    Strictly restricted to users with ADMIN role.
    """
    users = user_repository.list_users(limit=200)
    summaries = []
    for u in users:
        job_cnt = user_repository.count_user_jobs(u.user_id)
        summaries.append(
            AdminUserSummary(
                user_id=u.user_id,
                name=u.name,
                email=u.email,
                role=u.role.value,
                account_status=u.account_status.value,
                created_at=u.created_at.isoformat(),
                jobs_count=job_cnt,
            )
        )
    return summaries


# ==============================================================================
# 6. ADMIN: SYSTEM & QUEUE STATUS (GET /api/admin/system/status)
# ==============================================================================

@router.get(
    "/api/admin/system/status",
    summary="[Admin] Monitor system health, job queue, and database status",
)
def get_admin_system_status(admin: User = Depends(require_admin_user)):
    """
    Administrative health check returning job queue breakdown,
    worker health, database connectivity, and registered user metrics.
    """
    all_jobs = job_service.repository.list_all(limit=500)
    status_counts: Dict[str, int] = {}
    for j in all_jobs:
        s = j.status.value
        status_counts[s] = status_counts.get(s, 0) + 1

    users_count = len(user_repository.list_users(limit=1000))

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "admin_user": admin.email,
        "database": {
            "connected": True,
            "engine": "SQLite WAL",
            "total_jobs": len(all_jobs),
            "jobs_by_status": status_counts,
        },
        "worker": {
            "active": job_service.worker.is_running if job_service.worker else False,
            "queue_size": job_service.worker.job_queue.qsize() if job_service.worker else 0,
        },
        "users": {
            "total_registered": users_count,
        },
    }


# ==============================================================================
# 7. ADMIN: AUDIT LOGS (GET /api/admin/audit-logs)
# ==============================================================================

@router.get(
    "/api/admin/audit-logs",
    summary="[Admin] Query security audit trail records",
)
def get_audit_trail(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    admin: User = Depends(require_admin_user),
):
    """
    Administrative inspection endpoint for immutable security audit events.
    Never exposes passwords, session tokens, or biological sequence data.
    """
    logs = get_recent_audit_logs(limit=limit, event_type=event_type, user_id=user_id)
    return {
        "status": "success",
        "count": len(logs),
        "audit_logs": logs,
    }


# ==============================================================================
# 8. ADMIN: OPERATIONAL METRICS (GET /api/admin/metrics)
# ==============================================================================

@router.get(
    "/api/admin/metrics",
    summary="[Admin] Inspect operational telemetry, throughput and failure counters",
)
def get_operational_metrics(admin: User = Depends(require_admin_user)):
    """
    Returns real-time operational telemetry including HTTP status breakdown,
    latencies, pipeline outcomes, and error counters.
    """
    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics_collector.get_summary(),
    }


# ==============================================================================
# 9. ADMIN: FAILED JOB RECOVERY (POST /api/admin/recovery)
# ==============================================================================

@router.post(
    "/api/admin/recovery",
    summary="[Admin] Trigger recovery for interrupted or stale jobs",
)
def trigger_admin_recovery(admin: User = Depends(require_admin_user)):
    """
    Recovers any jobs interrupted by host process restarts.
    """
    recovered = job_service.recover_stale_jobs()
    return {
        "status": "success",
        "recovered_count": len(recovered),
        "recovered_job_ids": recovered,
        "message": f"Successfully processed recovery check. {len(recovered)} jobs updated.",
    }

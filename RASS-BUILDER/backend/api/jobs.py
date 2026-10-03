"""
RASS-BUILDER: Stage 7 & Stage 10 Job Processing & Queue API Endpoints
Provides asynchronous job creation, status polling, result retrieval, cancellation,
and job history endpoints with rate limiting, correlation tracking, and audit logging.
"""

from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request

from jobs.models import (
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
    JobStatus,
)
from jobs.service import job_service
from auth.models import User, UserRole
from auth.dependencies import get_current_user_optional
from core.correlation import get_current_request_id
from core.audit import record_audit_event, AuditEventType
from core.rate_limiter import enforce_rate_limit, get_client_ip
from core.metrics import metrics_collector


router = APIRouter(tags=["Stage 7 Asynchronous Jobs"])


def _check_job_access(job, current_user: Optional[User], request: Optional[Request] = None):
    """
    Data Isolation / IDOR Prevention:
    - If job has no user_id: legacy or guest unassigned job -> accessible.
    - If current_user is ADMIN: access permitted to all jobs.
    - If current_user is authenticated and job.user_id == current_user.user_id: access permitted.
    - If current_user is unauthenticated and job has user_id: 401 Unauthorized.
    - If current_user.user_id != job.user_id: 403 Forbidden.
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(request) if request else None

    if not job.user_id:
        return  # Legacy or guest unassigned job
    if not current_user:
        record_audit_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"target_job_id": job.job_id, "reason": "UNAUTHENTICATED"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.role == UserRole.ADMIN:
        return  # Admin access permitted
    if current_user.user_id != job.user_id:
        record_audit_event(
            event_type=AuditEventType.FORBIDDEN_ACCESS,
            status="FAILURE",
            user_id=current_user.user_id,
            request_id=req_id,
            ip_address=client_ip,
            details={"target_job_id": job.job_id, "owner_user_id": job.user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to access this resource.",
        )


# ==============================================================================
# 1. CREATE JOB (POST /api/jobs & /api/v1/jobs)
# ==============================================================================

@router.post(
    "/api/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("JOB_CREATION", max_requests=40, window_seconds=60))],
    summary="Enqueue an asynchronous genomic analysis job",
)
@router.post(
    "/api/v1/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit("JOB_CREATION", max_requests=40, window_seconds=60))],
    include_in_schema=False,
)
def create_job(
    request_obj: JobCreateRequest,
    req: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Submits a sequence or sequencing dataset for asynchronous pipeline execution.
    Associates the job with the authenticated user if available.
    Attaches correlation ID to trace request -> job -> result.
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(req)

    # 1. Validate file_path if provided to prevent path traversal
    if request_obj.file_path:
        raw_fp = request_obj.file_path.strip()
        if ".." in raw_fp or raw_fp.startswith("/") or (len(raw_fp) > 1 and raw_fp[1] == ":"):
            record_audit_event(
                event_type=AuditEventType.JOB_FAILED,
                status="FAILURE",
                user_id=current_user.user_id if current_user else None,
                request_id=req_id,
                ip_address=client_ip,
                details={"reason": "PATH_TRAVERSAL_DETECTED"},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path: path traversal is not permitted.",
            )

    try:
        user_id = current_user.user_id if current_user else None

        # Inject correlation ID into input_metadata
        if request_obj.options is None:
            request_obj.options = {}
        request_obj.options["request_id"] = req_id

        job, was_deduplicated = job_service.create_and_enqueue_job(request_obj, user_id=user_id)
        msg = (
            "Existing active analysis job returned (duplicate submission protected)."
            if was_deduplicated
            else "Analysis job queued successfully."
        )
        initial_status = job.status if was_deduplicated else JobStatus.QUEUED

        record_audit_event(
            event_type=AuditEventType.JOB_CREATED,
            status="SUCCESS",
            user_id=user_id,
            request_id=req_id,
            ip_address=client_ip,
            details={
                "job_id": job.job_id,
                "read_id": request_obj.read_id,
                "is_duplicate": was_deduplicated,
                "has_sequence": bool(request_obj.sequence),
                "has_file": bool(request_obj.file_path),
            },
        )

        metrics_collector.record_job_lifecycle("QUEUED")

        return JobCreateResponse(
            job_id=job.job_id,
            status=initial_status,
            message=msg,
            is_duplicate=was_deduplicated,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        metrics_collector.record_worker_error()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue analysis job: {str(exc)}",
        )


# ==============================================================================
# 2. JOB STATUS (GET /api/jobs/{job_id} & /api/v1/jobs/{job_id})
# ==============================================================================

@router.get(
    "/api/jobs/{job_id}",
    response_model=JobDetailResponse,
    summary="Poll status and progress of a genomic analysis job",
)
@router.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobDetailResponse,
    include_in_schema=False,
)
def get_job_status(
    job_id: str,
    req: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Returns current execution state, progress percentage, current pipeline stage,
    and sanitized status messaging for an analysis job.
    Enforces data isolation: users can only view their own jobs (Admins can view all).
    """
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    _check_job_access(job, current_user, req)
    return job.to_dict()


# ==============================================================================
# 3. JOB RESULT (GET /api/jobs/{job_id}/result & /api/v1/jobs/{job_id}/result)
# ==============================================================================

@router.get(
    "/api/jobs/{job_id}/result",
    summary="Retrieve completed Stage 5/6 structured analysis result",
)
@router.get(
    "/api/v1/jobs/{job_id}/result",
    include_in_schema=False,
)
def get_job_result(
    job_id: str,
    req: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Fetches the structured analysis results for a completed job.
    Enforces data isolation: users can only view their own results (Admins can view all).
    Returns HTTP 409 if the job is still active, or HTTP 400 if failed.
    """
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    _check_job_access(job, current_user, req)

    if job.status == JobStatus.COMPLETED:
        persisted_res = job_service.get_job_result(job_id)
        if persisted_res is not None:
            return persisted_res
        if job.result_reference is not None:
            return job.result_reference
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job completed but result reference could not be resolved.",
        )
    elif job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' is still in progress (status: {job.status.value}).",
        )
    elif job.status == JobStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' was cancelled.",
        )
    elif job.status == JobStatus.RECOVERY_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' requires recovery due to previous server restart: {job.error or job.message}",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' failed: {job.error or job.message}",
        )


# ==============================================================================
# 4. CANCEL JOB (POST /api/jobs/{job_id}/cancel & /api/v1/jobs/{job_id}/cancel)
# ==============================================================================

@router.post(
    "/api/jobs/{job_id}/cancel",
    response_model=JobDetailResponse,
    summary="Cancel a queued or active genomic analysis job",
)
@router.post(
    "/api/v1/jobs/{job_id}/cancel",
    response_model=JobDetailResponse,
    include_in_schema=False,
)
def cancel_job(
    job_id: str,
    req: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Safely marks an analysis job as cancelled and ceases further pipeline stages.
    Enforces authorization: users can only cancel their own jobs (Admins can cancel all).
    """
    req_id = get_current_request_id()
    client_ip = get_client_ip(req)

    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    _check_job_access(job, current_user, req)
    cancelled_job = job_service.cancel_job(job_id)

    record_audit_event(
        event_type=AuditEventType.JOB_CANCELLED,
        status="SUCCESS",
        user_id=current_user.user_id if current_user else None,
        request_id=req_id,
        ip_address=client_ip,
        details={"job_id": job_id},
    )
    metrics_collector.record_job_lifecycle("CANCELLED")

    return cancelled_job.to_dict()


# ==============================================================================
# 5. JOB HISTORY (GET /api/jobs & /api/v1/jobs)
# ==============================================================================

@router.get(
    "/api/jobs",
    response_model=List[JobSummaryResponse],
    summary="List recent genomic analysis jobs for history view",
)
@router.get(
    "/api/v1/jobs",
    response_model=List[JobSummaryResponse],
    include_in_schema=False,
)
def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Returns recent jobs sorted chronologically descending.
    If authenticated as standard USER: returns only user's own jobs.
    If authenticated as ADMIN: returns all jobs across workstation.
    Strictly sanitized: excludes raw sequences, filesystem paths, and internal stack traces.
    """
    user_filter = None
    if current_user:
        if current_user.role != UserRole.ADMIN:
            user_filter = current_user.user_id

    return job_service.list_jobs(limit=limit, user_id=user_filter)

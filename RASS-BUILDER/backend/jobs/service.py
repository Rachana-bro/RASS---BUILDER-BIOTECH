"""
RASS-BUILDER: Stage 7 Job Service
Orchestrates job lifecycle, idempotency/duplicate detection, queue scheduling, and retrieval.
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any

from .models import (
    Job,
    JobStatus,
    JobStage,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
)
from .repository import JobRepository, InMemoryJobRepository
from .worker import BackgroundJobWorker
from database.repository import SqliteJobRepository


class JobService:
    """
    Central service handling asynchronous genomic analysis jobs.
    Coordinates between API endpoints, persistent SQLite storage, and the background worker.
    """

    def __init__(
        self,
        repository: Optional[JobRepository] = None,
        worker: Optional[BackgroundJobWorker] = None,
    ):
        self.repository = repository or SqliteJobRepository()
        self.worker = worker or BackgroundJobWorker(self.repository)

    def generate_job_id(self) -> str:
        """Generates a distinct, readable job identifier."""
        return f"JOB-{uuid.uuid4().hex[:8].upper()}"

    def create_and_enqueue_job(
        self,
        request: JobCreateRequest,
        auto_enqueue: bool = True,
        user_id: Optional[str] = None,
    ) -> Tuple[Job, bool]:
        """
        Validates request, checks duplicate protection, creates job entity,
        and dispatches to the background worker.
        Returns: (job, was_deduplicated)
        """
        # Validate that either sequence or file_path is provided
        has_seq = bool(request.sequence and request.sequence.strip())
        has_file = bool(request.file_path and request.file_path.strip())

        if not has_seq and not has_file:
            raise ValueError("Either 'sequence' or 'file_path' must be provided for analysis.")

        # Duplicate job protection / idempotency lookup
        idempotency_key = request.idempotency_key
        if not idempotency_key and has_seq:
            # Deterministic fingerprint based on read_id and sequence content
            fp_payload = f"{request.read_id}:{request.sequence.strip()}".encode()
            idempotency_key = f"auto-{hashlib.sha256(fp_payload).hexdigest()[:16]}"

        if idempotency_key:
            existing = self.repository.find_by_idempotency_key(idempotency_key)
            if existing:
                now = datetime.now(timezone.utc)
                age_seconds = (now - existing.created_at).total_seconds()
                # Return existing job if currently active or completed within 60 seconds
                if existing.status in (JobStatus.QUEUED, JobStatus.RUNNING) or (
                    existing.status == JobStatus.COMPLETED and age_seconds < 60
                ):
                    return existing, True

        # Generate unique Job ID
        job_id = self.generate_job_id()

        seq_len = len(request.sequence.strip()) if has_seq else 0
        read_id = request.read_id or "READ_001"
        format_type = request.format or ("FASTQ" if has_file else "FASTA")

        # Initial sanitized metadata (no raw sequence or secrets)
        input_meta = {
            "read_id": read_id,
            "sequence_length": seq_len,
            "format": format_type,
            "has_file": has_file,
        }

        job = Job(
            job_id=job_id,
            status=JobStatus.QUEUED,
            current_stage=JobStage.QUEUED,
            progress=10,
            message="Analysis job queued successfully.",
            input_metadata=input_meta,
            raw_sequence=request.sequence,
            file_path=request.file_path,
            read_id=read_id,
            idempotency_key=idempotency_key,
            user_id=user_id,
        )

        self.repository.save(job)

        if auto_enqueue:
            self.worker.enqueue(job.job_id)

        return job, False

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieves job entity by unique job ID."""
        return self.repository.get(job_id)

    def cancel_job(self, job_id: str) -> Optional[Job]:
        """
        Safely cancels an active or queued job.
        If already completed or failed, preserves current state.
        """
        job = self.repository.get(job_id)
        if not job:
            return None

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return job

        job.cancelled = True
        job.status = JobStatus.CANCELLED
        job.current_stage = JobStage.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        job.message = "Job execution cancelled by user."
        self.repository.save(job)
        return job

    def list_jobs(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns recent jobs formatted for the job history table."""
        jobs = self.repository.list_all(limit=limit, user_id=user_id)
        return [j.to_summary_dict() for j in jobs]


    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves structured result object from persistent storage."""
        if hasattr(self.repository, "get_result"):
            return self.repository.get_result(job_id)
        job = self.get_job(job_id)
        return job.result_reference if job else None

    def recover_stale_jobs(self) -> List[str]:
        """Recovers any jobs interrupted in RUNNING state during server startup."""
        if hasattr(self.repository, "recover_stale_running_jobs"):
            return self.repository.recover_stale_running_jobs()
        return []

    def stop_worker(self) -> None:
        """Gracefully halts background worker thread on application shutdown."""
        if self.worker:
            self.worker.stop()

    def clear(self) -> None:
        """Clears stored jobs (used in tests)."""
        self.repository.clear()


# Global singleton instance for application use
job_service = JobService()

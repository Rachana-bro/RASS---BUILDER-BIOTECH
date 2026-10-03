"""
RASS-BUILDER: Stage 7 Job Repository Interface & In-Memory Implementation
Provides thread-safe persistence abstraction allowing seamless future database migration (Stage 8).
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import threading
from datetime import datetime, timezone

from .models import Job, JobStatus


class JobRepository(ABC):
    """Abstract storage interface for genomic analysis jobs."""

    @abstractmethod
    def save(self, job: Job) -> Job:
        """Persists or updates an existing job."""
        pass

    @abstractmethod
    def get(self, job_id: str) -> Optional[Job]:
        """Fetches a job by unique job ID."""
        pass

    @abstractmethod
    def list_all(self, limit: int = 50, user_id: Optional[str] = None) -> List[Job]:
        """Returns recent jobs sorted chronologically descending, optionally filtered by user_id."""
        pass

    @abstractmethod
    def find_by_idempotency_key(self, key: str) -> Optional[Job]:
        """Finds job matching the client idempotency key."""
        pass

    @abstractmethod
    def save_result(self, job_id: str, result: Dict[str, Any]) -> str:
        """Stores structured analysis result linked to a job."""
        pass

    @abstractmethod
    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves structured analysis result for a job."""
        pass

    @abstractmethod
    def recover_stale_running_jobs(self) -> List[str]:
        """Recovers jobs that were left in RUNNING status across restarts."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Empties repository (used in test isolation)."""
        pass


class InMemoryJobRepository(JobRepository):
    """
    Thread-safe in-memory job repository with RLock concurrency controls.
    Designed for fast, non-blocking asynchronous execution during Stage 7 and test isolation.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def save(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.job_id] = job
            return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_all(self, limit: int = 50, user_id: Optional[str] = None) -> List[Job]:
        with self._lock:
            jobs_to_sort = list(self._jobs.values())
            if user_id is not None:
                jobs_to_sort = [j for j in jobs_to_sort if j.user_id == user_id]
            sorted_jobs = sorted(
                jobs_to_sort,
                key=lambda j: j.created_at,
                reverse=True,
            )
            return sorted_jobs[:limit]


    def find_by_idempotency_key(self, key: str) -> Optional[Job]:
        if not key:
            return None
        with self._lock:
            for job in self._jobs.values():
                if job.idempotency_key == key:
                    return job
            return None

    def save_result(self, job_id: str, result: Dict[str, Any]) -> str:
        with self._lock:
            result_id = f"RES-{job_id}"
            self._results[job_id] = result
            if job_id in self._jobs:
                self._jobs[job_id].result_reference = result
            return result_id

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._results.get(job_id)

    def recover_stale_running_jobs(self) -> List[str]:
        recovered = []
        with self._lock:
            for job in self._jobs.values():
                if job.status == JobStatus.RUNNING:
                    from .models import JobStage
                    job.status = JobStatus.RECOVERY_REQUIRED
                    job.current_stage = JobStage.RECOVERY_REQUIRED
                    job.message = "Analysis process was interrupted by server restart. Manual recovery required."
                    job.error = "Execution interrupted by host process restart."
                    recovered.append(job.job_id)
        return recovered

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()
            self._results.clear()


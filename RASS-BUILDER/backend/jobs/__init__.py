"""
RASS-BUILDER: Stage 7 Asynchronous Job Processing & Queue Infrastructure
"""

from .models import (
    JobStatus,
    JobStage,
    Job,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobSummaryResponse,
)
from .repository import JobRepository, InMemoryJobRepository
from .worker import BackgroundJobWorker

__all__ = [
    "JobStatus",
    "JobStage",
    "Job",
    "JobCreateRequest",
    "JobCreateResponse",
    "JobDetailResponse",
    "JobSummaryResponse",
    "JobRepository",
    "InMemoryJobRepository",
    "BackgroundJobWorker",
    "JobService",
    "job_service",
]


def __getattr__(name):
    """PEP 562 dynamic attribute resolution to prevent circular import loops with database.repository."""
    if name == "JobService":
        from .service import JobService
        return JobService
    if name == "job_service":
        from .service import job_service
        return job_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

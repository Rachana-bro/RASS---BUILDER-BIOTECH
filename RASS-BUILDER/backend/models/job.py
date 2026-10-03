"""
RASS-BUILDER: AnalysisJob model compatibility layer.
Preserves Stage 4 AnalysisJob interface while integrating Stage 7 Job infrastructure.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from jobs.models import JobStatus, JobStage, Job


@dataclass
class AnalysisJob:
    """
    Stage 4 AnalysisJob dataclass with Stage 7 backward-compatible enhancements.
    """
    job_id: str
    status: str
    created_at: datetime
    progress: int
    message: str
    current_stage: str = "QUEUED"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_metadata: Dict[str, Any] = field(default_factory=dict)
    result_reference: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


__all__ = [
    "AnalysisJob",
    "JobStatus",
    "JobStage",
    "Job",
]

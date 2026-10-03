"""
RASS-BUILDER: Stage 7 Job Models & Schema Definitions
Defines core Job domain entity, status lifecycles, and API request/response schemas.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class JobStage(str, Enum):
    QUEUED = "QUEUED"
    DATA_INGESTION = "DATA_INGESTION"
    QUALITY_CONTROL = "QUALITY_CONTROL"
    TRANSFORMER_ANALYSIS = "TRANSFORMER_ANALYSIS"
    PATTERN_ANALYSIS = "PATTERN_ANALYSIS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


@dataclass
class Job:
    """
    Internal domain entity representing an asynchronous genomic analysis job.
    Sensitive payloads (raw_sequence, file_path) are strictly retained internally
    and NEVER serialized to public status APIs or job history listings.
    """
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    current_stage: JobStage = JobStage.QUEUED
    progress: int = 10
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    message: str = "Job accepted and queued for execution."
    input_metadata: Dict[str, Any] = field(default_factory=dict)
    raw_sequence: Optional[str] = None      # Internal worker payload
    file_path: Optional[str] = None         # Internal worker payload
    read_id: str = "READ_001"
    result_reference: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    idempotency_key: Optional[str] = None
    cancelled: bool = False
    user_id: Optional[str] = None           # Stage 9 User association

    def to_dict(self) -> Dict[str, Any]:
        """Serializes public status without exposing raw sequence or file paths."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_stage": self.current_stage.value,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_metadata": self.input_metadata,
            "error": self.error,
            "result_reference": self.result_reference,
            "user_id": self.user_id,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Serializes minimal metadata for job history table listing."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_stage": self.current_stage.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "message": self.message,
            "read_id": self.input_metadata.get("read_id", self.read_id),
            "sequence_length": self.input_metadata.get("sequence_length", 0),
            "user_id": self.user_id,
        }


# ==============================================================================
# PYDANTIC SCHEMAS FOR API CONTRACT
# ==============================================================================

class JobCreateRequest(BaseModel):
    sequence: Optional[str] = Field(None, description="DNA sequence string (A, C, G, T, N)")
    file_path: Optional[str] = Field(None, description="Server-side FASTQ file path to process")
    read_id: Optional[str] = Field("READ_001", description="Identifier of the sequence read")
    format: Optional[str] = Field("FASTA", description="Sequence format descriptor (FASTA / FASTQ)")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key to prevent duplicate runs")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pipeline configuration options")


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    is_duplicate: bool = False


class JobDetailResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    current_stage: str
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    input_metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    result_reference: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class JobSummaryResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    current_stage: str
    created_at: str
    completed_at: Optional[str] = None
    message: str
    read_id: Optional[str] = "READ_001"
    sequence_length: Optional[int] = 0
    user_id: Optional[str] = None


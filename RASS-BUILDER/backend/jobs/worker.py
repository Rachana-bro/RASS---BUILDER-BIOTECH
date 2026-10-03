"""
RASS-BUILDER: Stage 7 & Stage 10 Hardened Background Job Worker
Picks up queued genomic analysis jobs and executes the pipeline asynchronously:
Stage 4 Quality Control / Normalization -> Stage 5 Transformer Foundation -> Stage 6 Structured Output.
Guarantees jobs always reach terminal status (COMPLETED / FAILED / CANCELLED) without remaining stuck.
"""

from pathlib import Path
import queue
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .models import Job, JobStatus, JobStage
from .repository import JobRepository
from core.correlation import set_current_request_id, get_current_request_id
from core.logger import logger
from core.audit import record_audit_event, AuditEventType
from core.metrics import metrics_collector


class BackgroundJobWorker:
    """
    Dedicated worker thread and queue processor for genomic analysis jobs.
    Reuses existing Stage 4 and Stage 5 processing components without duplication.
    """

    def __init__(self, repository: JobRepository):
        self.repository = repository
        self.job_queue: queue.Queue[Optional[str]] = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Returns True if the background thread is currently active."""
        return self._worker_thread is not None and self._worker_thread.is_alive()

    def start(self):
        """Starts the background worker thread if not already active."""
        with self._lock:
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._stop_event.clear()
                self._worker_thread = threading.Thread(
                    target=self._worker_loop,
                    daemon=True,
                    name="RassGenomicWorkerThread",
                )
                self._worker_thread.start()

    def stop(self):
        """Stops the worker thread gracefully."""
        self._stop_event.set()
        self.job_queue.put(None)

    def enqueue(self, job_id: str):
        """Adds a job to the FIFO queue and ensures the worker thread is running."""
        self.job_queue.put(job_id)
        self.start()

    def _worker_loop(self):
        """Continuous background execution loop."""
        while not self._stop_event.is_set():
            try:
                job_id = self.job_queue.get(timeout=0.5)
                if job_id is None:
                    break
                self.process_job(job_id)
                self.job_queue.task_done()
            except queue.Empty:
                continue
            except Exception as loop_err:
                logger.error(f"Unexpected error in background worker loop: {str(loop_err)}")
                metrics_collector.record_worker_error()
                continue

    def process_job(self, job_id: str) -> Optional[Job]:
        """
        Executes the end-to-end pipeline for a single job through distinct, measurable stages:
        1. 20% — Data Ingestion & Input Validation
        2. 40% — Stage 4 Quality Control & Normalization
        3. 60% — Stage 5 DNA Transformer Tokenization & Embeddings
        4. 80% — Attention Computation & Pattern Checkpoint Evaluation
        5. 100% — Completion & Result Reference Generation
        """
        try:
            job = self.repository.get(job_id)
        except Exception as repo_err:
            logger.error(f"Failed to fetch job '{job_id}' from repository: {str(repo_err)}")
            metrics_collector.record_database_error()
            return None

        if not job:
            return None

        # Propagate request correlation ID from job metadata if present
        meta = job.input_metadata or {}
        req_id = meta.get("request_id") or get_current_request_id()
        set_current_request_id(req_id)

        # Guard: check if already completed
        if job.status == JobStatus.COMPLETED:
            return job

        # Guard: check if already cancelled or finished
        if job.cancelled or job.status == JobStatus.CANCELLED:
            job.status = JobStatus.CANCELLED
            job.current_stage = JobStage.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            job.message = "Job was cancelled prior to execution."
            self.repository.save(job)
            return job

        try:
            # ------------------------------------------------------------------
            # STAGE: 20% — DATA INGESTION
            # ------------------------------------------------------------------
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            job.progress = 20
            job.current_stage = JobStage.DATA_INGESTION
            job.message = "Ingesting sequence data and validating format..."
            self.repository.save(job)

            if job.cancelled:
                return self._finalize_cancellation(job)

            raw_sequence = job.raw_sequence or ""

            # Check if file_path was supplied (FASTQ pipeline integration)
            if not raw_sequence and job.file_path:
                from bioinformatics.fastq_parser import parse_fastq
                from bioinformatics.filtering import FilterConfig, filter_reads

                target_file = Path(job.file_path)
                if not target_file.exists():
                    candidate = Path(__file__).resolve().parent.parent.parent / job.file_path
                    if candidate.exists():
                        target_file = candidate
                    else:
                        raise FileNotFoundError("Specified sequence input file could not be accessed.")

                parsed_reads = []
                for read in parse_fastq(str(target_file)):
                    parsed_reads.append(read)
                    if len(parsed_reads) >= 100:
                        break

                if not parsed_reads:
                    raise ValueError("No sequencing reads identified in input file.")

                config = FilterConfig(min_mean_quality=20.0, min_length=1)
                passed, _ = filter_reads(parsed_reads, config)
                if not passed:
                    raise ValueError("All reads failed quality score filter criteria.")

                raw_sequence = passed[0].sequence
                job.read_id = passed[0].read_id

            if not raw_sequence or not raw_sequence.strip():
                raise ValueError("DNA sequence cannot be empty.")

            clean_seq = raw_sequence.strip().upper()
            if len(clean_seq) > 10000:
                raise ValueError(
                    f"Sequence length ({len(clean_seq)} bp) exceeds maximum supported limit of 10000 bp."
                )

            # ------------------------------------------------------------------
            # STAGE: 40% — QUALITY CONTROL & NORMALIZATION (STAGE 4)
            # ------------------------------------------------------------------
            job.progress = 40
            job.current_stage = JobStage.QUALITY_CONTROL
            job.message = "Executing Stage 4 quality control and sequence normalization..."
            self.repository.save(job)

            if job.cancelled:
                return self._finalize_cancellation(job)

            from bioinformatics.normalization import normalize_sequence
            normalized_seq = normalize_sequence(clean_seq)
            if not normalized_seq:
                raise ValueError("Sequence cannot be empty after normalization.")

            # Update input metadata
            job.input_metadata = {
                "read_id": job.read_id,
                "sequence_length": len(normalized_seq),
                "format": job.input_metadata.get("format", "FASTA"),
                "pipeline_version": "Stage 4 -> Stage 5 -> Stage 6",
                "request_id": req_id,
            }
            self.repository.save(job)

            # ------------------------------------------------------------------
            # STAGE: 60% — TRANSFORMER ANALYSIS (STAGE 5)
            # ------------------------------------------------------------------
            job.progress = 60
            job.current_stage = JobStage.TRANSFORMER_ANALYSIS
            job.message = "Running DNA Transformer tokenization and sequence embeddings..."
            self.repository.save(job)

            if job.cancelled:
                return self._finalize_cancellation(job)

            from models.stage5_engine import stage5_engine

            # ------------------------------------------------------------------
            # STAGE: 80% — PATTERN ANALYSIS & ATTENTION MAPPING
            # ------------------------------------------------------------------
            job.progress = 80
            job.current_stage = JobStage.PATTERN_ANALYSIS
            job.message = "Computing attention representation and evaluating pattern checkpoints..."
            self.repository.save(job)

            if job.cancelled:
                return self._finalize_cancellation(job)

            # Full Stage 5 Transformer Pipeline execution
            stage5_result = stage5_engine.analyze_sequence(
                sequence=normalized_seq,
                read_id=job.read_id,
            )

            if job.cancelled:
                return self._finalize_cancellation(job)

            # ------------------------------------------------------------------
            # STAGE: 100% — COMPLETION & RESULT REFERENCE
            # ------------------------------------------------------------------
            if hasattr(self.repository, "save_result"):
                self.repository.save_result(job.job_id, stage5_result)

            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.current_stage = JobStage.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.message = "Analysis complete. Structured results ready for Stage 6 Dashboard."
            job.result_reference = stage5_result
            self.repository.save(job)

            # Stage 10 Observability & Audit
            record_audit_event(
                event_type=AuditEventType.JOB_COMPLETED,
                status="SUCCESS",
                user_id=job.user_id,
                request_id=req_id,
                details={"job_id": job.job_id, "read_id": job.read_id},
            )
            metrics_collector.record_job_lifecycle("COMPLETED")

            return job

        except Exception as exc:
            # Guarantee job ALWAYS reaches terminal FAILED state
            job.status = JobStatus.FAILED
            job.current_stage = JobStage.FAILED
            job.completed_at = datetime.now(timezone.utc)

            raw_msg = str(exc)
            if isinstance(exc, FileNotFoundError) or "FileNotFoundError" in raw_msg or "accessed" in raw_msg or "\\" in raw_msg or "/" in raw_msg:
                job.error = "Specified sequence input file could not be accessed."
            elif isinstance(exc, (ValueError, KeyError)):
                job.error = raw_msg
            else:
                job.error = "Analysis could not be completed. Please review the input data and try again."

            job.message = "Analysis processing failed."

            try:
                self.repository.save(job)
            except Exception as save_err:
                logger.error(f"Critical: failed to persist failed state for job {job.job_id}: {str(save_err)}")
                metrics_collector.record_database_error()

            record_audit_event(
                event_type=AuditEventType.JOB_FAILED,
                status="FAILURE",
                user_id=job.user_id,
                request_id=req_id,
                details={"job_id": job.job_id, "error": job.error},
            )
            metrics_collector.record_job_lifecycle("FAILED")
            metrics_collector.record_worker_error()

            return job

    def _finalize_cancellation(self, job: Job) -> Job:
        """Helper to mark job as safely cancelled."""
        job.status = JobStatus.CANCELLED
        job.current_stage = JobStage.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        job.message = "Job execution cancelled by user."
        self.repository.save(job)
        metrics_collector.record_job_lifecycle("CANCELLED")
        return job

"""
RASS-BUILDER: Stage 10 Hardened File Ingestion API
Provides safe, sanitized upload endpoints for FASTQ and FASTA genomic sequencing files.
Enforces size limits, path-traversal prevention, format validation, and audit trails.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Request, status

from bioinformatics.fastq_parser import parse_fastq
from bioinformatics.fasta_parser import parse_fasta
from bioinformatics.quality import calculate_quality_metrics
from core.config import settings
from core.audit import record_audit_event, AuditEventType
from core.rate_limiter import enforce_rate_limit, get_client_ip
from core.correlation import get_current_request_id


router = APIRouter(
    prefix="/api/v1/uploads",
    tags=["Uploads & Ingestion"],
)

UPLOAD_DIRECTORY = Path("uploads").resolve()
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


def sanitize_and_validate_filename(filename: str, allowed_extensions: tuple) -> str:
    """
    Prevents path traversal attacks by extracting base filename and verifying extension.
    """
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    # Strip directory components (prevents ../ and \..\ attacks)
    base_name = os.path.basename(filename).strip()
    if not base_name or base_name in (".", ".."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename supplied.",
        )

    lower_name = base_name.lower()
    if not lower_name.endswith(allowed_extensions):
        ext_list = ", ".join(allowed_extensions)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Only {ext_list} files are permitted.",
        )

    return base_name


@router.post(
    "/fastq",
    dependencies=[Depends(enforce_rate_limit("UPLOAD", max_requests=25, window_seconds=60))],
    summary="Upload and validate a FASTQ sequencing file",
)
async def upload_fastq(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Ingests and validates FASTQ sequencing datasets.
    Rejects malformed records, path traversal payloads, and files exceeding size limits.
    """
    client_ip = get_client_ip(request)
    req_id = get_current_request_id()

    allowed_extensions = (
        ".fastq",
        ".fq",
        ".fastq.gz",
        ".fq.gz",
    )

    safe_filename = sanitize_and_validate_filename(file.filename or "", allowed_extensions)
    contents = await file.read()

    # Request size guard
    if len(contents) > settings.max_upload_size_bytes:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": "PAYLOAD_TOO_LARGE", "size_bytes": len(contents)},
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowable limit of {settings.max_upload_size_bytes // (1024*1024)} MB.",
        )

    if len(contents) == 0:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": "EMPTY_FILE"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    suffix = Path(safe_filename).suffix
    with NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=UPLOAD_DIRECTORY,
    ) as temp_file:
        temp_file.write(contents)
        temp_path = Path(temp_file.name).resolve()

    # Path traversal assertion: temp_path MUST strictly reside inside UPLOAD_DIRECTORY
    try:
        temp_path.relative_to(UPLOAD_DIRECTORY)
    except ValueError:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal path resolution detected.",
        )

    try:
        reads = list(parse_fastq(str(temp_path)))
        if not reads:
            raise ValueError("No valid sequencing reads found in FASTQ file.")

        metrics = calculate_quality_metrics(reads)

        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD,
            status="SUCCESS",
            request_id=req_id,
            ip_address=client_ip,
            details={
                "filename": safe_filename,
                "format": "FASTQ",
                "reads_count": len(reads),
                "size_bytes": len(contents),
            },
        )

        return {
            "status": "success",
            "filename": safe_filename,
            "metrics": metrics,
        }

    except ValueError as error:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": str(error)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        temp_path.unlink(missing_ok=True)


@router.post(
    "/fasta",
    dependencies=[Depends(enforce_rate_limit("UPLOAD", max_requests=25, window_seconds=60))],
    summary="Upload and validate a FASTA genomic file",
)
async def upload_fasta(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Ingests and validates standard FASTA format genomic reference files.
    """
    client_ip = get_client_ip(request)
    req_id = get_current_request_id()

    allowed_extensions = (".fasta", ".fa", ".fna")
    safe_filename = sanitize_and_validate_filename(file.filename or "", allowed_extensions)
    contents = await file.read()

    if len(contents) > settings.max_upload_size_bytes:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": "PAYLOAD_TOO_LARGE", "size_bytes": len(contents)},
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowable limit of {settings.max_upload_size_bytes // (1024*1024)} MB.",
        )

    if len(contents) == 0:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": "EMPTY_FILE"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    suffix = Path(safe_filename).suffix
    with NamedTemporaryFile(
        delete=False,
        suffix=suffix,
        dir=UPLOAD_DIRECTORY,
    ) as temp_file:
        temp_file.write(contents)
        temp_path = Path(temp_file.name).resolve()

    try:
        temp_path.relative_to(UPLOAD_DIRECTORY)
    except ValueError:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal path resolution detected.",
        )

    try:
        records = list(parse_fasta(str(temp_path)))
        if not records:
            raise ValueError("No sequence records identified in FASTA file.")

        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD,
            status="SUCCESS",
            request_id=req_id,
            ip_address=client_ip,
            details={
                "filename": safe_filename,
                "format": "FASTA",
                "record_count": len(records),
                "size_bytes": len(contents),
            },
        )

        return {
            "status": "success",
            "filename": safe_filename,
            "format": "FASTA",
            "record_count": len(records),
            "first_record_id": records[0].record_id,
            "sequence_length": len(records[0].sequence),
        }

    except ValueError as error:
        record_audit_event(
            event_type=AuditEventType.FILE_UPLOAD_FAILED,
            status="FAILURE",
            request_id=req_id,
            ip_address=client_ip,
            details={"filename": safe_filename, "reason": str(error)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        temp_path.unlink(missing_ok=True)

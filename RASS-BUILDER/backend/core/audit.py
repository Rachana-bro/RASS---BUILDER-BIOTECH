"""
RASS-BUILDER: Stage 10 Audit Logging Subsystem
Persists security-relevant audit trails into relational SQLite storage.
Strictly redacts credentials, session secrets, and genomic data before persistence.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

from .correlation import get_current_request_id
from .logger import logger


class AuditEventType:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    AUTH_FAILURE = "AUTH_FAILURE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    FORBIDDEN_ACCESS = "FORBIDDEN_ACCESS"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_UPLOAD_FAILED = "FILE_UPLOAD_FAILED"
    JOB_CREATED = "JOB_CREATED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    JOB_CANCELLED = "JOB_CANCELLED"
    ADMIN_ACTION = "ADMIN_ACTION"
    CONFIG_VALIDATION = "CONFIG_VALIDATION"


def sanitize_audit_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ensures no passwords, session tokens, cryptographic salts, or full
    DNA sequence strings are persisted into audit log records.
    """
    if not details:
        return {}

    sanitized = {}
    forbidden_keys = {
        "password",
        "confirm_password",
        "token",
        "access_token",
        "salt",
        "secret",
        "authorization",
        "raw_sequence",
    }

    for k, v in details.items():
        k_lower = str(k).lower()
        if k_lower in forbidden_keys:
            sanitized[k] = "[REDACTED]"
        elif k_lower in ("sequence", "dna_sequence") and isinstance(v, str):
            sanitized[k] = f"[SEQUENCE_LENGTH_{len(v)}BP]"
        elif isinstance(v, (str, int, float, bool, type(None))):
            sanitized[k] = v
        elif isinstance(v, dict):
            sanitized[k] = sanitize_audit_details(v)
        else:
            sanitized[k] = str(v)

    return sanitized


def record_audit_event(
    event_type: str,
    status: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> Optional[str]:
    """
    Records an immutable audit event in the database.
    Safe against exceptions to prevent audit failures from aborting business operations.
    """
    from database.connection import get_db_connection

    req_id = request_id or get_current_request_id()
    log_id = f"aud_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    safe_details = sanitize_audit_details(details)
    details_json = json.dumps(safe_details)

    try:
        with get_db_connection(db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (log_id, timestamp, event_type, user_id, request_id, status, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (log_id, now, event_type, user_id, req_id, status.upper(), ip_address, details_json),
            )
            conn.commit()

        logger.info(
            f"AUDIT [{status.upper()}] {event_type} - User: {user_id or 'anonymous'} | Req: {req_id}"
        )
        return log_id
    except Exception as exc:
        logger.error(f"Failed to record audit event '{event_type}': {str(exc)}")
        return None


def get_recent_audit_logs(
    limit: int = 50,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves recent audit logs for administrative inspection.
    """
    from database.connection import get_db_connection

    query = "SELECT * FROM audit_logs"
    params: List[Any] = []
    clauses: List[str] = []

    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY timestamp DESC LIMIT ?;"
    params.append(limit)

    with get_db_connection(db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    result = []
    for r in rows:
        try:
            parsed_details = json.loads(r["details"])
        except Exception:
            parsed_details = {}

        result.append(
            {
                "log_id": r["log_id"],
                "timestamp": r["timestamp"],
                "event_type": r["event_type"],
                "user_id": r["user_id"],
                "request_id": r["request_id"],
                "status": r["status"],
                "ip_address": r["ip_address"],
                "details": parsed_details,
            }
        )
    return result

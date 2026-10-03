"""
RASS-BUILDER: Stage 10 Core Security, Reliability & Observability Package
Exports centralized configurations, correlation tracking, structured logging,
audit logging, rate limiting, and telemetry metrics.
"""

from .config import settings, AppConfig
from .correlation import (
    CorrelationIdMiddleware,
    get_current_request_id,
    set_current_request_id,
    generate_request_id,
    request_id_ctx_var,
)
from .logger import logger, get_logger, redact_sensitive_data
from .audit import record_audit_event, get_recent_audit_logs, AuditEventType
from .rate_limiter import rate_limiter, enforce_rate_limit
from .metrics import metrics_collector
from .security_headers import SecurityHeadersMiddleware
from .error_handlers import register_error_handlers

__all__ = [
    "settings",
    "AppConfig",
    "CorrelationIdMiddleware",
    "get_current_request_id",
    "set_current_request_id",
    "generate_request_id",
    "request_id_ctx_var",
    "logger",
    "get_logger",
    "redact_sensitive_data",
    "record_audit_event",
    "get_recent_audit_logs",
    "AuditEventType",
    "rate_limiter",
    "enforce_rate_limit",
    "metrics_collector",
    "SecurityHeadersMiddleware",
    "register_error_handlers",
]

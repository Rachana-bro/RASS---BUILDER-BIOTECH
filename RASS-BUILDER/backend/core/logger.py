"""
RASS-BUILDER: Stage 10 Structured Logging & Redaction System
Provides JSON / structured logging with automatic masking of sensitive credentials,
session tokens, and large genomic sequence payloads.
"""

import re
import logging
import sys
from typing import Any
from .correlation import get_current_request_id
from .config import settings


# Sensitive pattern regexes for data redaction
RE_PASSWORD = re.compile(r'(password|confirm_password|secret|api_key|token|access_token)["\']?\s*[:=]\s*["\']?([^"\'\s,;]+)', re.IGNORECASE)
RE_BEARER = re.compile(r'Bearer\s+[A-Za-z0-9_\-\.]+', re.IGNORECASE)
RE_LONG_DNA = re.compile(r'\b[ACGTN]{51,}\b', re.IGNORECASE)


def redact_sensitive_data(message: str) -> str:
    """
    Redacts passwords, bearer tokens, and long genomic sequence strings (>50bp)
    from log messages to protect user privacy and sensitive biological data.
    """
    if not isinstance(message, str):
        message = str(message)

    # Mask passwords and secret fields
    message = RE_PASSWORD.sub(r'\1: [REDACTED]', message)
    # Mask Bearer tokens
    message = RE_BEARER.sub('Bearer [REDACTED_TOKEN]', message)
    # Mask long DNA sequences
    message = RE_LONG_DNA.sub(lambda m: f"[DNA_SEQUENCE_{len(m.group(0))}BP_MASKED]", message)

    return message


class RedactingFormatter(logging.Formatter):
    """
    Custom logging formatter that injects correlation request_id
    and scrubs sensitive credentials and sequence dumps.
    """

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or get_current_request_id()
        record.request_id = req_id

        # Redact message
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_sensitive_data(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive_data(str(a)) for a in record.args)

        formatted = super().format(record)
        return formatted


def get_logger(name: str = "rass_builder") -> logging.Logger:
    """
    Configures and returns a structured logger with correlation and redaction.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        level_str = settings.log_level
        log_level = getattr(logging, level_str, logging.INFO)
        logger.setLevel(log_level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        log_format = "%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s: %(message)s"
        formatter = RedactingFormatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger


# Global default logger instance
logger = get_logger("rass_builder")

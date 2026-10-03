"""
RASS-BUILDER: Stage 10 Request & Job Correlation System
Provides unique Request ID propagation across HTTP requests, structured logs,
and asynchronous background analysis jobs.
"""

import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


# Context variable holding correlation ID for the active async task / thread
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    """Generates a clean, unique request correlation ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_current_request_id() -> str:
    """Retrieves current request ID from contextvar or generates a fallback ID."""
    req_id = request_id_ctx_var.get()
    if not req_id:
        req_id = generate_request_id()
        request_id_ctx_var.set(req_id)
    return req_id


def set_current_request_id(req_id: str) -> None:
    """Explicitly sets the correlation ID in the contextvar."""
    request_id_ctx_var.set(req_id)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware ensuring every request has a correlation ID.
    Reads incoming X-Request-ID or X-Correlation-ID header, or generates a fresh ID.
    Injects the ID into request context and response headers.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or request.headers.get("x-request-id")
        )

        req_id = incoming_id.strip() if (incoming_id and incoming_id.strip()) else generate_request_id()
        request_id_ctx_var.set(req_id)
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

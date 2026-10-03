"""
RASS-BUILDER: Stage 10 Global Error Handling System
Provides uniform, structured error payloads across all HTTP exceptions and unhandled faults.
Strictly sanitizes responses to prevent leakage of stack traces, internal paths, or credentials.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .correlation import get_current_request_id
from .logger import logger
from .metrics import metrics_collector


def get_error_code_from_status(status_code: int) -> str:
    """Maps HTTP status codes to standardized error code strings."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return code_map.get(status_code, f"HTTP_{status_code}")


def register_error_handlers(app: FastAPI) -> None:
    """
    Registers custom exception handlers on the FastAPI application instance.
    Ensures dual compatibility:
    1. New Stage 10 structured format: `error: { code, message, request_id }`
    2. Backward-compatible top-level `detail` string for existing tests and clients.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = get_current_request_id()
        error_code = get_error_code_from_status(exc.status_code)
        message = str(exc.detail) if exc.detail else "An error occurred."

        # Pass through custom headers (e.g. WWW-Authenticate, Retry-After, etc.)
        headers = dict(exc.headers) if exc.headers else {}
        headers["X-Request-ID"] = req_id

        # Sanitize internal filesystem paths if accidentally in detail
        if "\\" in message or "/Users/" in message or "/home/" in message:
            message = "The requested resource could not be accessed."

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": error_code,
                    "message": message,
                    "request_id": req_id,
                },
                "detail": message,  # Backward compatibility with Starlette/FastAPI tests
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = get_current_request_id()
        # Extract clean error messages from pydantic validation errors
        errors = exc.errors()
        err_messages = []
        for e in errors:
            loc = " -> ".join([str(x) for x in e.get("loc", []) if x != "body"])
            msg = e.get("msg", "Invalid value")
            err_messages.append(f"{loc}: {msg}" if loc else msg)

        summary_msg = "; ".join(err_messages) if err_messages else "Request validation failed."

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": summary_msg,
                    "request_id": req_id,
                },
                "detail": errors,  # Standard FastAPI validation detail structure
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = get_current_request_id()
        # Structured server-side logging with request ID (never send stack trace to client)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path} (req_id: {req_id}): {type(exc).__name__}: {str(exc)}",
            exc_info=True,
        )
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=0.0,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please contact system administrator with the request ID.",
                    "request_id": req_id,
                },
                "detail": "Internal server error. Please retry or contact support with request ID.",
            },
            headers={"X-Request-ID": req_id},
        )

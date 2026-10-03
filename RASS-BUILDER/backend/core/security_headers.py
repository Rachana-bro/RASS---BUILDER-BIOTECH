"""
RASS-BUILDER: Stage 10 Security Headers & Request Guard Middleware
Injects production security headers, enforces maximum request payload size limits,
and tracks HTTP telemetry metrics.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .config import settings
from .metrics import metrics_collector
from .correlation import get_current_request_id


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies defense-in-depth HTTP security response headers and payload size guards.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        req_id = get_current_request_id()

        # 1. Request payload size guard
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_bytes = int(content_length)
                if length_bytes > settings.max_upload_size_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Payload size ({length_bytes} bytes) exceeds maximum allowable limit ({settings.max_upload_size_bytes} bytes).",
                                "request_id": req_id,
                            },
                            "detail": "Payload too large. Exceeds server upload limits.",
                        },
                        headers={"X-Request-ID": req_id},
                    )
            except ValueError:
                pass

        # 2. Process request through application pipeline
        response = await call_next(request)

        # 3. Telemetry recording
        duration_ms = (time.time() - start_time) * 1000.0
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        # 4. Inject Production Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        return response

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from loguru import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing and request ID"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Add request ID to request state
        request.state.request_id = request_id

        logger.info(f"[{request_id}] {request.method} {request.url.path} started")

        response = await call_next(request)

        process_time = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"]    = request_id
        response.headers["X-Process-Time"]  = f"{process_time}ms"

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"completed {response.status_code} in {process_time}ms"
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"]   = "nosniff"
        response.headers["X-Frame-Options"]          = "DENY"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"

        return response

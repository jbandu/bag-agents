"""
Logging Middleware

Logs all requests and responses passing through the gateway.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Logs request method, path, status code, and processing time.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        start_time = time.time()

        # Log request
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"← {request.method} {request.url.path} "
            f"→ {response.status_code} ({process_time:.3f}s)"
        )

        # Add custom header with processing time
        response.headers["X-Process-Time"] = str(process_time)

        return response

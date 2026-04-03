"""
Generic ASGI Middleware for LogEverything.

Works with any ASGI application (FastAPI, Starlette, Quart, etc.).
Provides automatic request correlation, logging, and timing.
"""

import logging
import time
from typing import Callable, Optional, Sequence, Set

from logeverything.correlation import (
    clear_correlation,
    set_correlation_id,
    set_request_context,
)


class LogEverythingASGIMiddleware:
    """
    ASGI middleware that adds correlation IDs and request logging.

    For each HTTP request the middleware will:

    1. Extract or generate a correlation ID from the configured header.
    2. Set correlation context (method, path, client IP).
    3. Log the request start.
    4. Capture the response status code and inject the correlation ID header.
    5. Log the request completion with timing.
    6. Clear correlation context.

    Args:
        app: The ASGI application to wrap.
        logger_name: Name of the logger to use.
        exclude_paths: Paths to skip (e.g. health checks).
        request_id_header: Header name for the correlation / request ID.
        log_request_body: Whether to log request bodies (default False).
        log_response_body: Whether to log response bodies (default False).
    """

    def __init__(
        self,
        app: Callable,
        logger_name: str = "logeverything.http",
        exclude_paths: Sequence[str] = ("/health", "/metrics"),
        request_id_header: str = "X-Request-ID",
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        self.app = app
        self.logger = logging.getLogger(logger_name)
        self.exclude_paths: Set[str] = set(exclude_paths)
        self.request_id_header = request_id_header
        self.request_id_header_lower = request_id_header.lower().encode("latin-1")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        # --- Extract or generate correlation ID ---
        headers = dict(scope.get("headers", []))
        incoming_id = headers.get(self.request_id_header_lower, b"").decode("latin-1", "replace")
        cid = set_correlation_id(incoming_id or None)

        method = scope.get("method", "WS")
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        set_request_context({"method": method, "path": path, "client_ip": client_ip})

        self.logger.info(">>> %s %s (client=%s)", method, path, client_ip)
        start = time.perf_counter()

        status_code: Optional[int] = None
        cid_header = (self.request_id_header.encode("latin-1"), cid.encode("latin-1"))

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                # Inject correlation header into the response
                resp_headers = list(message.get("headers", []))
                resp_headers.append(cid_header)
                message = {**message, "headers": resp_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            self.logger.exception(
                "<<< %s %s 500 (%.1fms) [unhandled exception]", method, path, duration_ms
            )
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            if status_code is not None:
                self.logger.info("<<< %s %s %s (%.1fms)", method, path, status_code, duration_ms)
            clear_correlation()

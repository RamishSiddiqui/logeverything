"""
Generic WSGI Middleware for LogEverything.

Works with any WSGI application (Flask, Django via WSGI, Bottle, etc.).
Provides automatic request correlation, logging, and timing.
"""

import logging
import time
from typing import Any, Callable, Iterable, Optional, Sequence, Set

from logeverything.correlation import clear_correlation, set_correlation_id, set_request_context


class LogEverythingWSGIMiddleware:
    """
    WSGI middleware that adds correlation IDs and request logging.

    Args:
        app: The WSGI application to wrap.
        logger_name: Name of the logger to use.
        exclude_paths: Paths to skip (e.g. health checks).
        request_id_header: HTTP header name for the correlation / request ID.
    """

    def __init__(
        self,
        app: Callable,
        logger_name: str = "logeverything.http",
        exclude_paths: Sequence[str] = ("/health", "/metrics"),
        request_id_header: str = "X-Request-ID",
    ):
        self.app = app
        self.logger = logging.getLogger(logger_name)
        self.exclude_paths: Set[str] = set(exclude_paths)
        self.request_id_header = request_id_header
        # WSGI normalises headers to HTTP_<NAME> with underscores
        self._wsgi_header_key = "HTTP_" + request_id_header.upper().replace("-", "_")

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        path = environ.get("PATH_INFO", "/")
        if path in self.exclude_paths:
            return self.app(environ, start_response)  # type: ignore[no-any-return]

        # --- Correlation ---
        incoming_id = environ.get(self._wsgi_header_key, "")
        cid = set_correlation_id(incoming_id or None)

        method = environ.get("REQUEST_METHOD", "GET")
        client_ip = environ.get("REMOTE_ADDR", "unknown")

        set_request_context({"method": method, "path": path, "client_ip": client_ip})

        self.logger.info(">>> %s %s (client=%s)", method, path, client_ip)
        start = time.perf_counter()

        status_code: Optional[str] = None

        def custom_start_response(status: str, response_headers: list, exc_info: Any = None) -> Any:
            nonlocal status_code
            status_code = status
            # Inject correlation header
            response_headers.append((self.request_id_header, cid))
            return start_response(status, response_headers, exc_info)

        try:
            response = self.app(environ, custom_start_response)
            return response  # type: ignore[no-any-return]
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

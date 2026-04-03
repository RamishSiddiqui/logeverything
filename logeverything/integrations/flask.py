"""
Flask extension for LogEverything.

Provides a Flask extension that hooks into ``before_request``,
``after_request``, and ``teardown_request`` for automatic correlation
and request logging.

Usage::

    from flask import Flask
    from logeverything.integrations.flask import LogEverythingFlask

    app = Flask(__name__)
    LogEverythingFlask(app)

    # Or with the application factory pattern:
    le = LogEverythingFlask()
    le.init_app(app)
"""

import logging
import time
from typing import Any, Optional, Sequence, Set

from logeverything.correlation import (
    clear_correlation,
    set_correlation_id,
    set_request_context,
)

try:
    from flask import Flask, g, request

    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False


class LogEverythingFlask:
    """
    Flask extension for automatic request correlation and logging.

    Args:
        app: Optional Flask application (pass ``None`` for factory pattern).
        logger_name: Name of the logger to use.
        exclude_paths: Paths to skip logging for.
        request_id_header: HTTP header name for request / correlation IDs.
    """

    def __init__(
        self,
        app: Optional["Flask"] = None,
        logger_name: str = "logeverything.http",
        exclude_paths: Sequence[str] = ("/health", "/metrics"),
        request_id_header: str = "X-Request-ID",
    ):
        self.logger = logging.getLogger(logger_name)
        self.exclude_paths: Set[str] = set(exclude_paths)
        self.request_id_header = request_id_header

        if app is not None:
            self.init_app(app)

    def init_app(self, app: "Flask") -> None:
        """Attach hooks to a Flask application."""
        if not _HAS_FLASK:
            raise RuntimeError("Flask is not installed. Install it with: pip install flask")

        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

    def _before_request(self) -> None:
        path = request.path
        if path in self.exclude_paths:
            g._le_skip = True
            return

        g._le_skip = False
        incoming_id = request.headers.get(self.request_id_header, "")
        cid = set_correlation_id(incoming_id or None)
        g._le_correlation_id = cid
        g._le_start_time = time.perf_counter()

        set_request_context(
            {
                "method": request.method,
                "path": path,
                "client_ip": request.remote_addr or "unknown",
            }
        )

        self.logger.info(
            ">>> %s %s (client=%s)",
            request.method,
            path,
            request.remote_addr,
        )

    def _after_request(self, response: Any) -> Any:
        if getattr(g, "_le_skip", True):
            return response

        duration_ms = (time.perf_counter() - g._le_start_time) * 1000
        self.logger.info(
            "<<< %s %s %s (%.1fms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )

        # Inject correlation header into response
        response.headers[self.request_id_header] = getattr(g, "_le_correlation_id", "")
        return response

    def _teardown_request(self, exception: Optional[BaseException] = None) -> None:
        if getattr(g, "_le_skip", True):
            return

        if exception is not None:
            self.logger.exception("Request failed with exception")

        clear_correlation()

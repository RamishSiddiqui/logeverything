"""
Django middleware for LogEverything.

Standard Django middleware that adds correlation IDs and request logging.

Usage — add to ``MIDDLEWARE`` in ``settings.py``::

    MIDDLEWARE = [
        ...
        "logeverything.integrations.django.LogEverythingDjangoMiddleware",
        ...
    ]

Optional settings (in ``settings.py``)::

    LOGEVERYTHING_LOGGER_NAME = "logeverything.http"
    LOGEVERYTHING_EXCLUDE_PATHS = {"/health", "/metrics"}
    LOGEVERYTHING_REQUEST_ID_HEADER = "X-Request-ID"
"""

import logging
import time
from typing import Any, Callable, Set

from logeverything.correlation import clear_correlation, set_correlation_id, set_request_context


class LogEverythingDjangoMiddleware:
    """
    Django middleware for automatic request correlation and logging.

    Follows the standard Django middleware protocol (``__init__`` / ``__call__`` /
    ``process_exception``).
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

        # Read optional Django settings with sensible defaults
        try:
            from django.conf import settings

            self.logger_name: str = getattr(
                settings, "LOGEVERYTHING_LOGGER_NAME", "logeverything.http"
            )
            self.exclude_paths: Set[str] = set(
                getattr(settings, "LOGEVERYTHING_EXCLUDE_PATHS", ("/health", "/metrics"))
            )
            self.request_id_header: str = getattr(
                settings, "LOGEVERYTHING_REQUEST_ID_HEADER", "X-Request-ID"
            )
        except Exception:
            self.logger_name = "logeverything.http"
            self.exclude_paths = {"/health", "/metrics"}
            self.request_id_header = "X-Request-ID"

        self.logger = logging.getLogger(self.logger_name)
        # Django normalises headers to META keys: HTTP_X_REQUEST_ID
        self._meta_key = "HTTP_" + self.request_id_header.upper().replace("-", "_")

    def __call__(self, request: Any) -> Any:
        path = request.path
        if path in self.exclude_paths:
            return self.get_response(request)

        # --- Correlation ---
        incoming_id = request.META.get(self._meta_key, "")
        cid = set_correlation_id(incoming_id or None)

        method = request.method
        client_ip = self._get_client_ip(request)

        set_request_context({"method": method, "path": path, "client_ip": client_ip})

        self.logger.info(">>> %s %s (client=%s)", method, path, client_ip)
        start = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            self.logger.exception(
                "<<< %s %s 500 (%.1fms) [unhandled exception]", method, path, duration_ms
            )
            raise
        finally:
            clear_correlation()

        duration_ms = (time.perf_counter() - start) * 1000
        self.logger.info("<<< %s %s %s (%.1fms)", method, path, response.status_code, duration_ms)

        # Inject correlation header
        response[self.request_id_header] = cid
        return response

    def process_exception(self, request: Any, exception: BaseException) -> None:
        """Log unhandled exceptions with correlation context."""
        self.logger.exception(
            "Unhandled exception in %s %s: %s",
            request.method,
            request.path,
            exception,
        )
        return None  # Let Django's default exception handling continue

    @staticmethod
    def _get_client_ip(request: Any) -> str:
        """Extract client IP, respecting X-Forwarded-For."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()  # type: ignore[no-any-return]
        return request.META.get("REMOTE_ADDR", "unknown")  # type: ignore[no-any-return]

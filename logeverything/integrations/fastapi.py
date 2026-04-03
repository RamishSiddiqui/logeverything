"""
FastAPI integration for LogEverything.

Provides a thin subclass of the ASGI middleware with FastAPI-friendly defaults
and a ``Depends()``-compatible request logger factory.
"""

import logging
from typing import Any, Sequence

from logeverything.correlation import get_correlation_id
from logeverything.integrations.asgi import LogEverythingASGIMiddleware

try:
    from starlette.requests import Request  # noqa: F401

    _HAS_STARLETTE = True
except ImportError:
    _HAS_STARLETTE = False


class LogEverythingMiddleware(LogEverythingASGIMiddleware):
    """
    FastAPI-flavoured ASGI middleware.

    Usage::

        from fastapi import FastAPI
        from logeverything.integrations.fastapi import LogEverythingMiddleware

        app = FastAPI()
        app.add_middleware(LogEverythingMiddleware)
    """

    def __init__(
        self,
        app: Any,
        logger_name: str = "logeverything.http",
        exclude_paths: Sequence[str] = ("/health", "/metrics", "/docs", "/openapi.json"),
        request_id_header: str = "X-Request-ID",
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        super().__init__(
            app,
            logger_name=logger_name,
            exclude_paths=exclude_paths,
            request_id_header=request_id_header,
            log_request_body=log_request_body,
            log_response_body=log_response_body,
        )


class _BoundRequestLogger:
    """Thin wrapper around a stdlib logger that carries the current correlation ID."""

    def __init__(self, logger: logging.Logger, correlation_id: str):
        self._logger = logger
        self.correlation_id = correlation_id

    def _log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.pop("extra", {})
        extra["correlation_id"] = self.correlation_id
        self._logger.log(level, msg, *args, extra=extra, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self._log(logging.ERROR, msg, *args, **kwargs)


def get_request_logger(
    logger_name: str = "logeverything.http",
) -> Any:
    """
    FastAPI dependency that returns a logger bound to the current request's
    correlation ID.

    Usage::

        from fastapi import Depends
        from logeverything.integrations.fastapi import get_request_logger

        @app.get("/users")
        async def get_users(log=Depends(get_request_logger())):
            log.info("Fetching users")  # auto-includes correlation_id
    """

    def _dependency() -> _BoundRequestLogger:
        cid = get_correlation_id()
        return _BoundRequestLogger(logging.getLogger(logger_name), cid)

    return _dependency

"""
Correlation Context for LogEverything.

Provides async-safe, thread-safe correlation ID propagation using contextvars.
This is the foundation for request tracing across middleware, transports, and dashboards.

Key Features:
- ContextVar-based correlation IDs (async-safe, same pattern as indent_manager.py)
- Request context propagation (method, path, client)
- CorrelationFilter for automatic LogRecord injection
- Thread propagation decorator for executor-based workloads
"""

import functools
import logging
import os
from contextvars import ContextVar, copy_context
from typing import Any, Callable, Dict, Optional

# --- Context Variables ---

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})


# --- Public API ---


def set_correlation_id(cid: Optional[str] = None) -> str:
    """
    Set or auto-generate a correlation ID for the current context.

    Args:
        cid: An explicit correlation ID. If None, a 16-char hex ID is generated.

    Returns:
        The correlation ID that was set.
    """
    if cid is None:
        cid = os.urandom(8).hex()
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    """
    Get the current correlation ID.

    Returns:
        The correlation ID, or empty string if unset.
    """
    return _correlation_id.get()


def set_request_context(ctx: Dict[str, Any]) -> None:
    """
    Set request context metadata for the current context.

    Typical keys: ``method``, ``path``, ``client_ip``.

    Args:
        ctx: Dictionary of request metadata.
    """
    _request_context.set(ctx)


def get_request_context() -> Dict[str, Any]:
    """
    Get the current request context metadata.

    Returns:
        Dictionary of request metadata, or empty dict if unset.
    """
    return _request_context.get()


def clear_correlation() -> None:
    """Reset all correlation state for the current context."""
    _correlation_id.set("")
    _request_context.set({})


# --- logging.Filter ---


class CorrelationFilter(logging.Filter):
    """
    A logging filter that auto-injects correlation context into every LogRecord.

    Adds the following attributes to each record:
    - ``correlation_id``
    - ``request_method``
    - ``request_path``

    Usage::

        import logging
        from logeverything.correlation import CorrelationFilter

        handler = logging.StreamHandler()
        handler.addFilter(CorrelationFilter())
        logger = logging.getLogger("myapp")
        logger.addHandler(handler)
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Inject correlation fields into the log record."""
        record.correlation_id = _correlation_id.get()
        ctx = _request_context.get()
        record.request_method = ctx.get("method", "")
        record.request_path = ctx.get("path", "")
        return True


# --- Thread Propagation ---


def propagate_context(func: Callable) -> Callable:
    """
    Decorator that copies the current contextvars into a new thread.

    Use this when dispatching work to ``concurrent.futures.ThreadPoolExecutor``
    or ``threading.Thread`` to ensure correlation IDs follow the call.

    Example::

        from logeverything.correlation import propagate_context

        @propagate_context
        def background_task():
            # get_correlation_id() returns the caller's ID here
            ...

        executor.submit(background_task)
    """
    ctx = copy_context()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return ctx.run(func, *args, **kwargs)

    return wrapper

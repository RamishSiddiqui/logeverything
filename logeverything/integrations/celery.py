"""
Celery integration for LogEverything.

Connects to Celery signals to provide automatic task logging with
correlation ID propagation across task chains and groups.

Usage::

    from celery import Celery
    from logeverything.integrations.celery import setup_celery_logging

    app = Celery("myapp")
    setup_celery_logging(app)
"""

import logging
import time
from typing import Any, Dict, Optional

from logeverything.correlation import (
    clear_correlation,
    get_correlation_id,
    set_correlation_id,
    set_request_context,
)

try:
    from celery import Celery
    from celery.signals import (
        before_task_publish,
        task_failure,
        task_postrun,
        task_prerun,
        task_retry,
    )

    _HAS_CELERY = True
except ImportError:
    _HAS_CELERY = False


def setup_celery_logging(
    app: Any,
    logger_name: str = "logeverything.celery",
) -> None:
    """
    Wire LogEverything into Celery's signal system.

    Args:
        app: A Celery application instance.
        logger_name: Logger name for task log messages.

    Raises:
        RuntimeError: If celery is not installed.
    """
    if not _HAS_CELERY:
        raise RuntimeError("Celery is not installed. Install it with: pip install celery")

    logger = logging.getLogger(logger_name)
    _task_start_times: Dict[str, float] = {}

    @before_task_publish.connect
    def _propagate_correlation(headers: Optional[Dict] = None, **kwargs: Any) -> None:
        """Inject current correlation ID into task headers for chain propagation."""
        if headers is None:
            return
        cid = get_correlation_id()
        if cid:
            headers.setdefault("le_correlation_id", cid)

    @task_prerun.connect
    def _on_task_prerun(task_id: str, task: Any, **kwargs: Any) -> None:
        # Restore propagated correlation or use task_id
        cid = getattr(task.request, "le_correlation_id", None)
        if not cid:
            # Check headers dict (Celery 4+)
            headers = getattr(task.request, "headers", None) or {}
            cid = headers.get("le_correlation_id")
        set_correlation_id(cid or task_id)

        set_request_context(
            {
                "method": "TASK",
                "path": task.name,
                "client_ip": "",
            }
        )

        _task_start_times[task_id] = time.perf_counter()
        logger.info(">>> TASK %s [%s]", task.name, task_id)

    @task_postrun.connect
    def _on_task_postrun(task_id: str, task: Any, state: str = "", **kwargs: Any) -> None:
        start = _task_start_times.pop(task_id, None)
        duration_ms = (time.perf_counter() - start) * 1000 if start else 0
        logger.info("<<< TASK %s [%s] %s (%.1fms)", task.name, task_id, state, duration_ms)
        clear_correlation()

    @task_failure.connect
    def _on_task_failure(task_id: str, exception: BaseException, task: Any, **kwargs: Any) -> None:
        logger.error("TASK FAILED %s [%s]: %s", task.name, task_id, exception, exc_info=exception)

    @task_retry.connect
    def _on_task_retry(request: Any, reason: Any, **kwargs: Any) -> None:
        logger.warning("TASK RETRY %s [%s]: %s", request.task, request.id, reason)

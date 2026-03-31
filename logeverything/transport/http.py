"""
HTTP Transport Handler for LogEverything.

Ships structured log records to a dashboard or collector via HTTP POST
using only the standard library (``urllib.request``). Zero external deps.

Usage::

    from logeverything.transport.http import HTTPTransportHandler

    handler = HTTPTransportHandler("http://dashboard:8999/api/ingest/logs")
    logger.addHandler(handler)
"""

import datetime
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from logeverything.transport.buffer import LogBuffer


class HTTPTransportHandler(logging.Handler):
    """
    Logging handler that batches records and POSTs them as JSON to an HTTP
    endpoint.

    Args:
        endpoint: URL to POST batched logs to (e.g.
                  ``http://localhost:8999/api/ingest/logs``).
        api_key: Optional API key sent as ``Authorization: Bearer <key>``.
        batch_size: Records per HTTP request.
        flush_interval: Seconds between automatic flushes.
        source_name: Identifier for this application / process (defaults to PID).
        max_retries: Retry count for failed HTTP POSTs.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        batch_size: int = 50,
        flush_interval: float = 2.0,
        source_name: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 10.0,
        level: int = logging.NOTSET,
    ):
        super().__init__(level)
        self.endpoint = endpoint
        self.api_key = api_key
        self.source_name = source_name or f"pid-{os.getpid()}"
        self.timeout = timeout

        self._buffer = LogBuffer(
            send_batch=self._send_batch,
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_retries=max_retries,
        )

    def emit(self, record: logging.LogRecord) -> None:
        """Serialize the record and queue it for batched delivery."""
        try:
            entry = self._record_to_dict(record)
            self._buffer.put(entry)
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        """Flush the internal buffer immediately."""
        self._buffer.flush()

    def close(self) -> None:
        """Flush remaining records and release resources."""
        self._buffer.close()
        super().close()

    # --- Internals ---

    def _record_to_dict(self, record: logging.LogRecord) -> Dict[str, Any]:
        entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", ""),
            "thread": record.thread,
            "process": record.process,
            "source": self.source_name,
        }
        if not entry["correlation_id"]:
            try:
                from logeverything.correlation import get_correlation_id

                entry["correlation_id"] = get_correlation_id()
            except Exception:
                pass
        return entry

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        payload = json.dumps({"logs": batch, "source": self.source_name}).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")

        urllib.request.urlopen(req, timeout=self.timeout)

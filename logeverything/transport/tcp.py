"""
TCP Transport Handler for LogEverything.

Ships newline-delimited JSON over a persistent TCP socket.
Suitable for high-reliability use within a private network.

Usage::

    from logeverything.transport.tcp import TCPTransportHandler

    handler = TCPTransportHandler("collector.internal", 5140)
    logger.addHandler(handler)
"""

import datetime
import json
import logging
import os
import socket
import threading
from typing import Any, Dict, List, Optional

from logeverything.transport.buffer import LogBuffer


class TCPTransportHandler(logging.Handler):
    """
    Logging handler that sends newline-delimited JSON over a persistent TCP
    connection with automatic reconnection.

    Args:
        host: Target host.
        port: Target port.
        batch_size: Records per write batch.
        flush_interval: Seconds between automatic flushes.
        source_name: Identifier for this process.
        max_retries: Retry count for failed sends.
        connect_timeout: TCP connect timeout in seconds.
    """

    def __init__(
        self,
        host: str,
        port: int,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        source_name: Optional[str] = None,
        max_retries: int = 3,
        connect_timeout: float = 5.0,
        level: int = logging.NOTSET,
    ):
        super().__init__(level)
        self.host = host
        self.port = port
        self.source_name = source_name or f"pid-{os.getpid()}"
        self.connect_timeout = connect_timeout

        self._sock: Optional[socket.socket] = None
        self._sock_lock = threading.Lock()

        self._buffer = LogBuffer(
            send_batch=self._send_batch,
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_retries=max_retries,
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = self._record_to_dict(record)
            self._buffer.put(entry)
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        self._buffer.flush()

    def close(self) -> None:
        self._buffer.close()
        self._close_socket()
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

    def _ensure_socket(self) -> socket.socket:
        """Return an open socket, reconnecting if needed."""
        if self._sock is not None:
            return self._sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.connect_timeout)
        sock.connect((self.host, self.port))
        self._sock = sock
        return sock

    def _close_socket(self) -> None:
        with self._sock_lock:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        data = b""
        for entry in batch:
            data += json.dumps(entry).encode("utf-8") + b"\n"

        with self._sock_lock:
            try:
                sock = self._ensure_socket()
                sock.sendall(data)
            except Exception:
                # Force reconnect on next attempt
                self._close_socket()
                raise

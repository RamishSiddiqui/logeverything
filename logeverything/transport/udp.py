"""
UDP Transport Handler for LogEverything.

Fire-and-forget JSON datagrams over UDP.
Suitable for high-throughput scenarios where occasional loss is acceptable.

Usage::

    from logeverything.transport.udp import UDPTransportHandler

    handler = UDPTransportHandler("collector.internal", 5141)
    logger.addHandler(handler)
"""

import datetime
import json
import logging
import os
import socket
from typing import Any, Dict, List, Optional

from logeverything.transport.buffer import LogBuffer


class UDPTransportHandler(logging.Handler):
    """
    Logging handler that sends JSON-encoded log records as UDP datagrams.

    Each record is sent as a single datagram (up to ~64 KB). Batching is still
    used to amortise serialisation overhead, but each record in the batch is
    sent as its own datagram so loss is bounded.

    Args:
        host: Target host.
        port: Target port.
        batch_size: Records to dequeue at once (each still sent individually).
        flush_interval: Seconds between automatic flushes.
        source_name: Identifier for this process.
        max_packet_size: Maximum UDP payload size in bytes. Records larger than
                         this are silently dropped.
    """

    def __init__(
        self,
        host: str,
        port: int,
        batch_size: int = 100,
        flush_interval: float = 2.0,
        source_name: Optional[str] = None,
        max_packet_size: int = 65000,
        level: int = logging.NOTSET,
    ):
        super().__init__(level)
        self.host = host
        self.port = port
        self.source_name = source_name or f"pid-{os.getpid()}"
        self.max_packet_size = max_packet_size

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._buffer = LogBuffer(
            send_batch=self._send_batch,
            batch_size=batch_size,
            flush_interval=flush_interval,
            max_retries=0,  # fire-and-forget
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
        try:
            self._sock.close()
        except Exception:
            pass  # nosec B110 -- best-effort socket cleanup
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
                pass  # nosec B110 -- best-effort correlation lookup
        return entry

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        for entry in batch:
            data = json.dumps(entry).encode("utf-8")
            if len(data) <= self.max_packet_size:
                self._sock.sendto(data, (self.host, self.port))
